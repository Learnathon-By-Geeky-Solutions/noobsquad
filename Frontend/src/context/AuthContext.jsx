import { createContext, useContext, useState, useEffect } from "react";
import { fetchUser } from "../api/auth"; // Import user fetch function

// ✅ Provide default context to avoid `undefined` issues
export const AuthContext = createContext({
  user: null,
  login: () => {},
  logout: () => {},
  loading: true,
});

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true); // ✅ Add loading state

  useEffect(() => {
    const loadUser = async () => {
      try {
        const token = localStorage.getItem("token"); // ✅ Ensure token exists
        if (!token) throw new Error("No token found");

        const response = await fetchUser(token);
        setUser(response.data);
      } catch (error) {
        console.error("Failed to fetch user:", error);
      } finally {
        setLoading(false);
      }
    };

    loadUser();
  }, []);

  const login = async (token) => {
    localStorage.setItem("token", token);
    try {
      const response = await fetchUser(token); // ✅ Ensure login updates user state
      setUser(response.data);
    } catch (error) {
      console.error("Failed to fetch user after login:", error);
    }
  };

  const logout = () => {
    localStorage.removeItem("token");
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, login, logout, loading }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};