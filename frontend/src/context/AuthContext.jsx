import { createContext, useContext, useState, useEffect, useMemo, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { fetchUser } from "../api/auth";

const AuthContext = createContext({
  user: null,
  profileCompleted: false,
  login: async () => {},
  logout: () => {},
  loading: true,
});

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [profileCompleted, setProfileCompleted] = useState(false);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    const loadUser = async () => {
      const token = localStorage.getItem("token");
      if (!token) {
        console.warn("No token found");
        setLoading(false);
        return;
      }

      try {
        console.log("Fetching user with token:", token);
        const userData = await fetchUser(token);
        setUser(userData);
        setProfileCompleted(userData.profile_completed);
      } catch (error) {
        console.error("Failed to fetch user:", error);
        logout();
      } finally {
        setLoading(false);
      }
    };

    loadUser();
  }, []);

  const login = useCallback(async (token) => {
    localStorage.setItem("token", token);
    try {
      const response = await fetchUser(token);
      const userData = response.data || response; 

      setUser(userData);
      setProfileCompleted(userData.profile_completed);

      navigate(userData.profile_completed ? "/dashboard" : "/complete-profile");
    } catch (error) {
      console.error("Failed to fetch user after login:", error);
    }
  }, [navigate]);

  const logout = useCallback(() => {
    console.log("Logging out...");
    localStorage.removeItem("token");
    setUser(null);
    setProfileCompleted(false);
    navigate("/login");
  }, [navigate]);

  const contextValue = useMemo(
    () => ({ user, profileCompleted, login, logout, loading }),
    [user, profileCompleted, login, logout, loading]
  );

  return <AuthContext.Provider value={contextValue}>{children}</AuthContext.Provider>;
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};
