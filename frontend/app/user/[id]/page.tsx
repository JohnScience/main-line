"use client";

import { useParams } from "next/navigation";

export default function UserPage() {
    const { id: userId } = useParams<{ id: string }>();

    return (
        <div>
            <h1>User Profile for user with id {userId}</h1>
            {/* Render user information */}
        </div>
    );
}
