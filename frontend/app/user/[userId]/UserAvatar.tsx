"use client";

import Image from "next/image";

import { startTransition, useActionState, useEffect } from "react";

import { toast } from "sonner";
import { handleUploadAvatarToServer } from "./actions";

function uploadAvatarToServer(file: File, uploadAvatarAction: (payload: FormData) => void) {
    let formData = new FormData();
    formData.append("avatar", file);
    console.log(formData);
    console.log(formData.get("avatar"));
    startTransition(() => {
        uploadAvatarAction(formData);
    });
}

function makeAvatarImgReader(
    file: File,
    uploadAvatarAction: (payload: FormData) => void,
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
        uploadAvatarToServer(file, uploadAvatarAction);
    };

    reader.onerror = () => {
        toast.error("Failed to read the selected avatar image file.");
    };

    return reader;
}

function startSelectingProfilePicture(
    uploadAvatarAction: (payload: FormData) => void,
    supportedImgFormats: string
) {
    const input = document.createElement("input");
    input.type = "file";
    input.accept = supportedImgFormats;
    input.onchange = (event: Event) => {
        const target = event.target as HTMLInputElement;
        const file = target.files?.[0];
        if (!file) {
            return;
        }

        const reader = makeAvatarImgReader(file, uploadAvatarAction, (percent) => {
            console.log(`Loading avatar image: ${percent}%`);
        });
        reader.readAsArrayBuffer(file);
    };
    input.click();
}

export function UserAvatar({ avatarUrl, supportedImgFormats }: { avatarUrl: string | null; supportedImgFormats: string }) {
    const [avatarUploadOutcome, uploadAvatarAction, isAvatarUploadPending] = useActionState(handleUploadAvatarToServer, undefined);

    useEffect(() => {
        if (!avatarUploadOutcome) {
            return;
        }
        switch (avatarUploadOutcome.kind) {
            case "Success": break;
            case "BadRequest": {
                toast.error("Failed to upload avatar due to client implementation error. This issue has been logged.");
                console.error(`Failed to upload avatar: ${avatarUploadOutcome.detail}`);
                break;
            };
            case "Unauthorized": {
                toast.error("Uploading the avatar is impossible while you are not logged in.");
                console.error("Uploading the avatar is impossible while you are not logged in.");
                break;
            };
            case "InternalServerError": {
                const errorMessage = `Failed to upload avatar due to server error${(avatarUploadOutcome.detail ? `: ${avatarUploadOutcome.detail}.` : ".")}`;
                toast.error(errorMessage);
                console.error(errorMessage);
                break;
            };
        }
    }, [avatarUploadOutcome]);

    return <Image
        // src={`/api/users/${viewedUserId}/avatar`}
        src={avatarUrl || "/account.svg"}
        alt="User Avatar"
        width={150}
        height={150}
        className="rounded-full w-full h-full object-cover cursor-pointer hover:brightness-75 transition-all duration-200"
        onClick={() => startSelectingProfilePicture(uploadAvatarAction, supportedImgFormats)}
    />

}