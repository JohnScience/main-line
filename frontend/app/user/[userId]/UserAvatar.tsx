"use client";

import Image from "next/image";
import { toast } from "sonner";

function uploadAvatarToServer(file: File) {
    let formData = new FormData();
    formData.append("avatar", file);
    console.log(`Uploading ${file.size} bytes avatar image ${file.name} to server...`);
}

function makeAvatarImgReader(
    file: File,
    updateProgress: (percent: number) => void
): FileReader {
    const reader = new FileReader();
    reader.onprogress = (event: ProgressEvent<FileReader>) => {
        if (event.lengthComputable) {
            const percentLoaded = Math.round((event.loaded / event.total) * 100);
            updateProgress(percentLoaded);
        }
    };
    reader.onload = () => {
        const contents = reader.result as ArrayBuffer;
        uploadAvatarToServer(file);
    };

    reader.onerror = () => {
        toast.error("Failed to read the selected avatar image file.");
    };

    return reader;
}

function startSelectingProfilePicture(supportedImgFormats: string) {
    const input = document.createElement("input");
    input.type = "file";
    input.accept = supportedImgFormats;
    input.onchange = (event: Event) => {
        const target = event.target as HTMLInputElement;
        const file = target.files?.[0];
        if (!file) {
            return;
        }

        const reader = makeAvatarImgReader(file, (percent) => {
            console.log(`Loading avatar image: ${percent}%`);
        });
        reader.readAsArrayBuffer(file);
    };
    input.click();
}

export function UserAvatar({ avatarUrl, supportedImgFormats }: { avatarUrl: string | null; supportedImgFormats: string }) {
    return <Image
        // src={`/api/users/${viewedUserId}/avatar`}
        src={avatarUrl || "/account.svg"}
        alt="User Avatar"
        width={150}
        height={150}
        className="rounded-full w-full h-full object-cover cursor-pointer hover:brightness-75 transition-all duration-200"
        onClick={() => startSelectingProfilePicture(supportedImgFormats)}
    />

}