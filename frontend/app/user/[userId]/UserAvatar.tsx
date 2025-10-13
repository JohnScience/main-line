"use client";

import { startTransition, useActionState, useEffect, useState } from "react";

import { toast } from "sonner";
import { handleUploadAvatarToServer } from "./actions";

function uploadAvatarToServer(file: File, uploadAvatarAction: (payload: FormData) => void) {
    let formData = new FormData();
    formData.append("avatar", file);
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

export function UserAvatar({ startingAvatarUrl, supportedImgFormats }: { startingAvatarUrl: string | null; supportedImgFormats: string }) {
    const [avatarUploadOutcome, uploadAvatarAction, isAvatarUploadPending] = useActionState(handleUploadAvatarToServer, undefined);

    const [avatarUrl, setAvatarUrl] = useState<string>(startingAvatarUrl || "/account.svg");

    useEffect(() => {
        if (!avatarUploadOutcome) {
            return;
        }
        switch (avatarUploadOutcome.kind) {
            case "Success": {
                setAvatarUrl(avatarUploadOutcome.url);
                toast.success("Avatar uploaded successfully.");
                break;
            };
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

    // next/image is terrible rn
    // See <https://www.reddit.com/r/nextjs/comments/ue5i5x/should_i_just_use_img_instead_of_image/>
    return <img
        // https://stackoverflow.com/questions/1077041/refresh-image-with-a-new-one-at-the-same-url
        src={avatarUrl}
        alt="User Avatar"
        width={150}
        height={150}
        className="rounded-full w-[250px] h-[250px] object-cover cursor-pointer hover:brightness-75 transition-all duration-200"
        onClick={() => startSelectingProfilePicture(uploadAvatarAction, supportedImgFormats)}
    />
}