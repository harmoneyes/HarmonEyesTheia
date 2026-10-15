/**
 * Copyright 2023 Tobii AB
 */
export declare const checkFrameResolution: (frameWidth: number, frameHeight: number) => void;
/**
 * Replace numeric codes in license failure messages with their symbolic names.
 * - "... error: N" -> ERROR_*
 * - "... result: N" -> LICENSE_VALIDATION_RESULT_*
 * Code 0 is intentionally not mapped.
 */
export declare function normalizeLicenseMessage(text: string): string;
