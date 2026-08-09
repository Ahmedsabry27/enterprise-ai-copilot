import { Amplify } from "aws-amplify";

const localHosts = new Set(["localhost", "127.0.0.1", "::1"]);
const isLocal = localHosts.has(window.location.hostname);
const localRedirect = window.location.origin;
const productionRedirect = import.meta.env.VITE_AUTH_REDIRECT_URI;
const userPoolId = import.meta.env.VITE_COGNITO_USER_POOL_ID || "us-east-1_4LsWwbt7e";
const userPoolClientId = import.meta.env.VITE_COGNITO_CLIENT_ID || "6kc3pqe9vkoalel08uintmo640";
const oauthDomain = import.meta.env.VITE_COGNITO_DOMAIN || "us-east-14lswwbt7e.auth.us-east-1.amazoncognito.com";

if (!isLocal && (!productionRedirect || !import.meta.env.VITE_COGNITO_USER_POOL_ID || !import.meta.env.VITE_COGNITO_CLIENT_ID || !import.meta.env.VITE_COGNITO_DOMAIN)) {
  throw new Error("Production Cognito configuration is incomplete");
}

Amplify.configure({
  Auth: {
    Cognito: {
      userPoolId,
      userPoolClientId,
      loginWith: {
        oauth: {
          domain: oauthDomain,
          scopes: ["openid", "email"],
          redirectSignIn: [
            isLocal
              ? localRedirect
              : productionRedirect,
          ],
          redirectSignOut: [
            isLocal
              ? localRedirect
              : productionRedirect,
          ],
          responseType: "code",
        },
      },
    },
  },
});
