import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';

import { expect, test } from '@playwright/test';
import ts from 'typescript';

import { BACKEND_URL } from '../playwright.config';

/**
 * Technical-integrity check: the frontend's Pattern and Gate value sets must
 * equal the backend's enums exactly. Nothing else enforces this link across
 * the stack.
 *
 * Scope is deliberately narrow: this fails if a letter or enum value drifts,
 * and says nothing about whether the display labels are good.
 *
 * The frontend arrays are read by parsing the source rather than importing
 * it, so this check cannot be fooled by a module that happens to export the
 * right thing at runtime.
 */

const TAXONOMY_PATH = fileURLToPath(new URL('../src/api/taxonomy.ts', import.meta.url));

/** Pull a `const NAME = [...] as const` string array out of a TypeScript file. */
function extractStringArray(sourcePath: string, name: string): string[] {
  const source = readFileSync(sourcePath, 'utf8');
  const file = ts.createSourceFile(sourcePath, source, ts.ScriptTarget.Latest, true);

  let found: string[] | null = null;

  const visit = (node: ts.Node): void => {
    if (ts.isVariableDeclaration(node) && node.name.getText() === name) {
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
      const frontend = extractStringArray(TAXONOMY_PATH, frontendConst);

      // Order is not part of the contract.
      expect(new Set(frontend).size, `${frontendConst} contains duplicates`).toBe(frontend.length);
      expect(new Set(backend).size, `backend ${schemaName} contains duplicates`).toBe(
        backend.length,
      );
      expect([...frontend].sort()).toEqual([...backend].sort());
    });
  }
});
