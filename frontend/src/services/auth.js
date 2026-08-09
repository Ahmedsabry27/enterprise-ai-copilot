import {
    signOut,
    signInWithRedirect,
    fetchAuthSession,
    getCurrentUser,
} from "aws-amplify/auth";

export async function logout() {
    await signOut();
}

export async function login() {
    await signInWithRedirect();
}

export async function getAccessToken() {
    if (import.meta.env.MODE === "e2e") {
        return window.sessionStorage.getItem("e2e_access_token");
    }
    const session = await fetchAuthSession();
    const token = session.tokens?.accessToken?.toString();

    if (import.meta.env.DEV) {
        console.log("[auth] Cognito access token present?", !!token);
        if (!token) {
            console.warn("No Cognito access token available from auth session");
        }
    }

    return token;
}

export async function getSession() {
    return await fetchAuthSession();
}

export async function currentUser() {
    if (import.meta.env.MODE === "e2e" && window.sessionStorage.getItem("e2e_access_token")) {
        return { username: "e2e-user", userId: "e2e-user" };
    }
    return await getCurrentUser();
}
