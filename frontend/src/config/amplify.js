import { Amplify } from "aws-amplify";

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
            "http://localhost:5173",
          ],
          redirectSignOut: [
            "http://localhost:5173",
          ],
          responseType: "code",
        },
      },
    },
  },
});