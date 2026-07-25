import { useEffect, useState } from "react";
import MainLayout from "./components/layout/MainLayout";
import { currentUser, login } from "./services/auth";

function App() {
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const checkAuthentication = async () => {
      try {
        // Check whether the user already has a valid session
        await currentUser();

        // User is authenticated
        setLoading(false);
      } catch (error) {
        console.log("User not authenticated. Redirecting to Cognito...");

        try {
          await login();
        } catch (loginError) {
          console.error("Login redirect failed:", loginError);
          setLoading(false);
        }
      }
    };

    checkAuthentication();
  }, []);

  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-semibold">
            Enterprise AI Copilot
          </h1>

          <p className="mt-4 text-muted-foreground">
            Authenticating...
          </p>
        </div>
      </div>
    );
  }

  return <MainLayout />;
}

export default App;