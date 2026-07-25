import { Button } from "@/components/ui/button";
import { login } from "@/services/auth";

export default function LoginPage() {
  return (
    <div className="flex h-screen items-center justify-center">
      <div className="rounded-xl border p-10 shadow-lg text-center">
        <h1 className="text-3xl font-bold">
          Enterprise AI Copilot
        </h1>

        <p className="mt-4 text-muted-foreground">
          Please sign in using your company account.
        </p>

        <Button
          className="mt-8"
          onClick={login}
        >
          Sign in
        </Button>
      </div>
    </div>
  );
}