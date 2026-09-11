import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';

import { expect, test } from '@playwright/test';
import ts from 'typescript';

import { BACKEND_URL } from '../playwright.config';

/**
 * Technical-integrity check: the frontend's Pattern and Gate value sets must
 * equal the backend's enums exactly.
 *
 * These two are the one link in the Pattern/Gate chain that nothing else
 * enforces. The other links already are:
 *
 *   - content/patterns.ts against the frontend's own Pattern/Gate types, by
 *     `as const satisfies Record<Pattern, ...>` at compile time
 *   - seeded case tags against the backend enums, by Python's own typing on
 *     CaseTaggedPattern / CaseTaggedGate
 *
 * Scope is deliberately narrow. This fails if a letter or enum value ever
 * drifts; it says nothing whatsoever about whether the display labels are
 * good, which is a content judgement and not a test's business.
 *
 * The frontend arrays are read by parsing the source rather than importing
 * it: src/api/student.ts imports boot/api, which dereferences `window.env` at
 * module scope and throws under Node. Parsing also means this check cannot be
 * fooled by a module that happens to export the right thing at runtime.
 */

const STUDENT_API_PATH = fileURLToPath(new URL('../src/api/student.ts', import.meta.url));

/** Pull a `const NAME = [...] as const` string array out of a TypeScript file. */
function extractStringArray(sourcePath: string, name: string): string[] {
  const source = readFileSync(sourcePath, 'utf8');
  const file = ts.createSourceFile(sourcePath, source, ts.ScriptTarget.Latest, true);

  let found: string[] | null = null;

  const visit = (node: ts.Node): void => {
    if (ts.isVariableDeclaration(node) && node.name.getText() === name) {
      // Unwrap `[...] as const` to reach the array literal itself.
      let initializer = node.initializer;
      if (initializer !== undefined && ts.isAsExpression(initializer)) {
        initializer = initializer.expression;
      }
      if (initializer !== undefined && ts.isArrayLiteralExpression(initializer)) {
        found = initializer.elements.map((element) => {
          if (!ts.isStringLiteral(element)) {
            throw new Error(
              `${name} in ${sourcePath} contains a non-string-literal member ` +
                `(${element.getText()}); this check only understands literal arrays.`,
            );
          }
          return element.text;
        });
      }
    }
    ts.forEachChild(node, visit);
  };

  visit(file);

  if (found === null) {
    throw new Error(
      `Could not find a string-literal array named ${name} in ${sourcePath}. ` +
        `If it was renamed or moved, update this check -- do not delete it.`,
    );
  }
  return found;
}

interface OpenApiSchema {
  components?: { schemas?: Record<string, { enum?: unknown[] }> };
}

/** Read one enum's members out of the live OpenAPI document. */
function enumFromSchema(schema: OpenApiSchema, name: string): string[] {
  const members = schema.components?.schemas?.[name]?.enum;
  if (!Array.isArray(members)) {
    throw new Error(
      `/openapi.json has no enum for schema ${name}. The backend enum may ` +
        `have been renamed, or it is no longer referenced by any endpoint.`,
    );
  }
  return members.map(String);
}

test.describe('Pattern and Gate stay identical across the stack', () => {
  for (const [schemaName, frontendConst] of [
    ['Pattern', 'PATTERNS'],
    ['Gate', 'GATES'],
  ] as const) {
    test(`${schemaName} matches the frontend's ${frontendConst}`, async ({ request }) => {
      const response = await request.get(`${BACKEND_URL}/openapi.json`);
      expect(response.ok(), `/openapi.json returned ${response.status()}`).toBe(true);

      const backend = enumFromSchema((await response.json()) as OpenApiSchema, schemaName);
      const frontend = extractStringArray(STUDENT_API_PATH, frontendConst);

      // Sorted set comparison in both directions: a member added on either
      // side, removed from either side, or renamed fails here. Order is not
      // part of the contract, so it is normalised away.
      expect(new Set(frontend).size, `${frontendConst} contains duplicates`).toBe(
        frontend.length,
      );
      expect(new Set(backend).size, `backend ${schemaName} contains duplicates`).toBe(
        backend.length,
      );
      expect([...frontend].sort()).toEqual([...backend].sort());
    });
  }
});
