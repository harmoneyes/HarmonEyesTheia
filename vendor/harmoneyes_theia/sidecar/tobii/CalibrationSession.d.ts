/**
 * Copyright 2023 Tobii AB
 */
import { FrameFormat, CalibrationPoint } from './types.js';
import { AlgoModule, InternalWebcamEyeTracker } from './nexus_wasm.js';
export declare const ERRMSG_NO_CALIB_CAP = "The application's Nexus Web license does not include the calibration capability.";
export declare class CalibrationSession {
    private readonly algoModule;
    private readonly internalWET;
    private readonly onCalibrationStopped;
    private calibrationStopped;
    private frameProcessor;
    constructor(algoModule: AlgoModule, internalWET: InternalWebcamEyeTracker, onCalibrationStopped: () => void, frameWidth: number, frameHeight: number, frameFormat: FrameFormat);
    /**
     * Send a webcam frame and calibration point coordinates to provide calibration data
     * to the eye tracker. Results from the analysis will be
     * emitted through the `gaze` observable.
     * @param frameData raw frame data - ensure that the data are in the same format
     * as specified when constructing the EyeTracker object
     * @param calibrationPoint the point on screen that is being calibrated
     * @param options.frameWidth the width [px] of the provided frame. if this is not specified, the frameWidth
     * specified in a previous send[Calibration]Frame call or when creating the associated EyeTracker object
     * will be used
     * @param options.frameHeight the width [px] of the provided frame. if this is not specified, the frameHeight
     * previously specified will be used
     * @param options.frameFormat the format of the provided frame. if this is not specified, the frameFormat
     * previously specified will be used
     * @returns an object with keys 'collectionSuccess' (true if calibration data were succesfully
     * collected from frame, otherwise false) and 'collectionAtPointFinished' (true if enough
     * calibration frames have been collected at point, otherwise false)
     */
    sendCalibrationFrame: (frameData: Uint8Array | Uint8ClampedArray, calibrationPoint: CalibrationPoint, options?: {
        frameWidth?: number;
        frameHeight?: number;
        frameFormat?: FrameFormat;
    }) => {
        collectionSuccess: boolean;
        collectionAtPointFinished: boolean;
    };
    /**
     * Compute a calibration based on data collected so far (with sendCalibrationFrame)
     * and apply the resulting calibration to the associated eye tracker.
     */
    computeAndApply: () => void;
    /**
     * Signal that the calibration session has been completed and no
     * further calls to this session's methods will be done.
     */
    stop: () => void;
    private assertHasNotStopped;
}
