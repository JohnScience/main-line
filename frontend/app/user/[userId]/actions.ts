import { postUploadUserAvatar } from "api-client";

export async function handleUploadAvatarToServer(previousState: unknown, formData: FormData):
    Promise<ReturnType<typeof postUploadUserAvatar>> {

    const avatarFile = formData.get("avatar") as File;
    if (!avatarFile) {
        throw new Error("No avatar file provided");
    }

    if (avatarFile.size > 5 * 1024 * 1024) { // 5 MB limit
        throw new Error("Avatar file size exceeds the 5MB limit");
    }

    const newFormData = new FormData();
    newFormData.append("avatar", avatarFile);

    const res = await postUploadUserAvatar({
        body: newFormData
    });

    return res;
}