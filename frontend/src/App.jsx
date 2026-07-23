import ChatPage from "./pages/ChatPage";
import ProtectedRoute from "./auth/ProtectedRoute";

function App() {
    return (
        <ProtectedRoute>
            <ChatPage />
        </ProtectedRoute>
    );
}

export default App;