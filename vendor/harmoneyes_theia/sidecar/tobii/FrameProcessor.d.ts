/**
 * Copyright 2023 Tobii AB
 */
import { FrameFormat, FrameSpecifications, CalibrationPoint } from './types.js';
import { AlgoModule, CalibrationOutput, InternalWebcamEyeTracker, TrackingOutput } from './nexus_wasm.js';
export declare class FrameProcessor {
    private readonly algoModule;
    private readonly internalWET;
    frameWidth: number;
    frameHeight: number;
    frameFormat: FrameFormat;
    private internalFrameFormat;
    private frameDataSize;
    private imagePointer;
    constructor(algoModule: AlgoModule, internalWET: InternalWebcamEyeTracker, frameWidth: number, frameHeight: number, frameFormat: FrameFormat);
    private updateFrameSettings;
    private allocImagePointer;
    processRegularFrame: (frameData: Uint8Array | Uint8ClampedArray, timestamp: number, options?: FrameSpecifications) => TrackingOutput;
    processCalibrationFrame: (frameData: Uint8Array | Uint8ClampedArray, timestamp: number, stimulusPoint: CalibrationPoint, options?: FrameSpecifications) => CalibrationOutput;
    destroy: () => void;
}
