/**
 * Copyright 2023 Tobii AB
 */
/**
 * webcam frame color format. GRAYSCALE: 1-channel grayscale. RGB: 3-channel color. RGBA: 4-channel color.
 */
export declare enum FrameFormat {
    GRAYSCALE = 0,
    RGB = 1,
    RGBA = 2
}
/**
 * Point on the screen, in normalized (0 to 1) coordinates, that the user is
 * currently looking at. {x: 0, y: 0} corresponds to the top left and
 * {x: 1, y: 1} corresponds to the bottom right. For default timestamps,
 * time elapsed between epoch and browser start is based on Date.now() meaning
 * it may be fairly inaccurate, while time since browser start (and between
 * timestamps) is based on the more reliable performance.now().
 * @member {(number|undefined)} x horizontal screen coordinate
 * @member {(number|undefined)} y vertical screen coordinate
 * @member {boolean} valid true if gaze point is valid, otherwise false (in which case 'x' and 'y'  are undefined)
 * @member {number} timestamp a user-defined timestamp value passed in when calling
 * `eyeTracker.sendFrame` or, if no such value was passed, the number of milliseconds that had
 * elapsed since the epoch when `sendFrame` was called
 * @member {object} userData contains user-defined key-value pairs that were passed in as the 'userData' object
 * when calling `eyeTracker.sendFrame`
 */
export interface Gaze {
    x: number | undefined;
    y: number | undefined;
    valid: boolean;
    timestamp: number;
    userData: object;
}
export interface FrameSpecifications {
    frameWidth?: number;
    frameHeight?: number;
    frameFormat?: FrameFormat;
}
/**
 * Represents a point, in normalized (0-1) coordinates, at which calibration is to be done.
 * @member {number} x horizontal screen coordinate
 * @member {number} y vertical screen coordinate
 *  */
export interface CalibrationPoint {
    x: number;
    y: number;
}
export interface GazeSubscription {
    unsubscribe: () => void;
}
