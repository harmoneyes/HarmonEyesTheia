/**
 * Copyright 2023 Tobii AB
 */
import { FrameFormat, Gaze, GazeSubscription } from './types.js';
import { CalibrationSession } from './CalibrationSession.js';
export declare class WebcamEyeTracker {
    private screenWidthMm;
    private screenHeightMm;
    private readonly fieldOfViewAngle;
    private static readonly NOT_READY_ERRMSG;
    ready: Promise<any>;
    private algoModule;
    private readyResolved;
    private timeOriginInEpochTime;
    private isCalibrating;
    private readonly gazeSubscribers;
    private frameProcessor;
    private internalWET;
    /**
     *
     * @param frameWidth width, in pixels, of webcam frames that will be fed with `sendFrame` (maximum of 1920)
     * @param frameHeight height of webcam frames that will be fed (maximum of 1080)
     * @param frameFormat color format of webcam frames that will be fed. defaults to RGB
     * @param screenWidthMm width, in millimeters, of device screen that filmed subject is looking at
     * @param screenHeightMm height of screen/display
     * @param fieldOfViewAngle webcam diagonal field of view angle, in degrees (about 75 for most regular webcams)
     * @param licenseInformation license key content as received from Tobii
     */
    constructor(frameWidth: number, frameHeight: number, frameFormat: FrameFormat | undefined, screenWidthMm: number, screenHeightMm: number, fieldOfViewAngle: number, licenseInformation: string);
    get frameSettings(): {
        width: number | undefined;
        height: number | undefined;
        format: FrameFormat | undefined;
    };
    get screenSettings(): {
        widthMm: number;
        heightMm: number;
    };
    get cameraFieldOfViewAngle(): number;
    /**
     * Update the the screen settings of the screen your application is running on. Correct screen settings
     * are required for good eye tracking results.
     * @param screenWidthMm Screen width in mm.
     * @param screenHeightMm Screen height in mm.
     */
    updateScreenSettings: (screenWidthMm: number, screenHeightMm: number) => void;
    /**
     * Subscribe a callback to the Gaze stream. All subscribers are continuously called
     * with Gaze objects, representing gaze x/y position on the screen, resulting from
     * analysis of `sendFrame` input.
     * @returns a subscription with a single method, unsubscribe, which may be called to
     * unsubscribe the subscriber from the Gaze stream
     */
    subscribeToGaze: (subscriber: (gaze: Gaze) => void) => GazeSubscription;
    /**
     * Unsubscribe a callback from the Gaze stream. If the callback is not
     * currently subscribed to the stream, nothing happens.
     */
    unsubscribeFromGaze: (subscriber: (gaze: Gaze) => void) => void;
    /**
     * Send a webcam frame for eye tracking analysis. Results from the analysis will be
     * emitted through the `gaze` observable.
     * @param frameData raw frame data - ensure that the data are in the same format
     * as specified when constructing the EyeTracker object
     * @param options.timestamp value that will be included as timestamp [ms] of resulting Gaze
     * emitted to gaze subscribers. note that this value is optional but strongly recommended.
     * if no value is provided, a best-effort value for time at which `sendFrame` was called
     * will be generated instead.
     * @param options.userData an object with user-defined key-value pairs which will be included with
     * the resulting Gaze emitted to subscribers
     * @param options.frameWidth the width [px] of the provided frame. if this is not specified, the frameWidth
     * specified in a previous sendFrame call or when creating the EyeTracker object will be used
     * @param options.frameHeight the width [px] of the provided frame. if this is not specified, the frameHeight
     * previously specified will be used
     * @param options.frameFormat the format of the provided frame. if this is not specified, the frameFormat
     * previously specified will be used
     * @returns true if eye data were successfully extracted from frame, otherwise false
     */
    sendFrame: (frameData: Uint8Array | Uint8ClampedArray, options?: {
        timestamp?: number;
        userData?: object;
        frameWidth?: number;
        frameHeight?: number;
        frameFormat?: FrameFormat;
    }) => boolean;
    /**
     * Emit 'complete' event to subscribers and do clean up.
     */
    destroy: () => void;
    /**
     * Start the calibration process, placing the tracker in a state ready
     * to receive data collection requests.
     * @returns an object through which all commands for the calibration session
     * are issued - before `.stop` is called on this object, no calls
     * to the eye tracker object's methods are permitted
     */
    calibrationStart: () => CalibrationSession;
    /**
     * Retrieve raw data of the currently applied calibration. This is used to reapply
     * the same calibration at a later time (e.g. after the browser session is reset)
     * by calling `WebcamEyeTracker.applyCalibration`. If this method is called
     * before a calibration session has been performed, it returns the default
     * (not tailored for any particular individual) calibration data.
     * @returns an array which is to later be passed in as-is to `.applyCalibration`
     */
    calibrationRetrieve: () => Uint8Array;
    /**
     * Apply a previous calibration.
     * @param calibrationData array of calibration data previously retrieved with `calibrationRetrieve`
     */
    calibrationApply: (calibrationData: Uint8Array) => void;
    private calibrationStop;
    private assertIsNotCalibrating;
}
