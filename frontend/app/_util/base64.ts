export function base64ToUint8Array(base64String: string): Uint8Array {
    // Decode the Base64 string into a binary string
    const binaryString = atob(base64String);

    // Create a Uint8Array from the binary string
    // Each character's charCodeAt(0) value represents a byte
    const uint8Array = Uint8Array.from(binaryString, char => char.charCodeAt(0));

    return uint8Array;
}
