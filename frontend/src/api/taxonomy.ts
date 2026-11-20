/**
 * The fixed taxonomy both routes share, mirroring backend api/models/enums.py.
 * e2e/enum-consistency.spec.ts checks PATTERNS and GATES against the backend.
 *
 * Array order is picker order.
 */
export const PATTERNS = [
  'A',
  'B',
  'C',
  'D',
  'E',
  'F',
  'G',
  'H',
  'I',
  'J',
  'K',
  'L',
  'M',
  'N',
  'O',
  'P',
] as const;
export type Pattern = (typeof PATTERNS)[number];

export const GATES = ['G1', 'G2', 'G3', 'G4', 'G5', 'G6'] as const;
export type Gate = (typeof GATES)[number];

export type ContrastType = 'twin_counter_case' | 'open_area';

export const DOMAINS = [
  'Material Science',
  'Advanced Manufacturing / 3D Printing',
  'Semiconductors and Nanotechnology',
  'Artificial Intelligence',
  'Cyber Technologies',
  'Quantum Technology',
  'Robotics & Autonomous Systems',
  'Neurotechnology',
  'Biochemistry',
] as const;
export type Domain = (typeof DOMAINS)[number];

export const FUNCTIONS = [
  'sensing',
  'generating',
  'controlling',
  'predicting',
  'editing',
  'optimizing',
  'fabricating',
  'computing',
] as const;
export type Function = (typeof FUNCTIONS)[number];

export const FORMS = [
  'platform',
  'model',
  'dataset',
  'protocol',
  'device',
  'infrastructure',
  'material',
  'method',
] as const;
export type Form = (typeof FORMS)[number];
