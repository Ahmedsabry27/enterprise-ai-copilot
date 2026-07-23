import { Amplify } from "aws-amplify";

const isLocal = window.location.hostname === "localhost";

Amplify.configure({
  Auth: {
    Cognito: {
      userPoolId: "us-east-1_4LsWwbt7e",
      userPoolClientId: "6kc3pqe9vkoalel08uintmo640",
      loginWith: {
        oauth: {
          domain: "us-east-14lswwbt7e.auth.us-east-1.amazoncognito.com",
          scopes: ["openid", "email"],
          redirectSignIn: [
            isLocal
              ? "http://localhost:5173"
              : "https://main.d3nubels63r4fu.amplifyapp.com",
          ],
          redirectSignOut: [
            isLocal
              ? "http://localhost:5173"
              : "https://main.d3nubels63r4fu.amplifyapp.com",
          ],
          responseType: "code",
        },
      },
    },
  },
});