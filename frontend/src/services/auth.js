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
    const session = await fetchAuthSession();
    return session.tokens?.accessToken?.toString();
}

export async function getSession() {
    return await fetchAuthSession();
}

export async function currentUser() {
    return await getCurrentUser();
}