import { useEffect, useRef } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { api } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";

export default function AuthCallback() {
  const location = useLocation();
  const navigate = useNavigate();
  const { setUser } = useAuth();
  const processed = useRef(false);

  useEffect(() => {
    if (processed.current) return;
    processed.current = true;

    const hash = location.hash || "";
    const match = hash.match(/session_id=([^&]+)/);
    if (!match) {
      navigate("/login", { replace: true });
      return;
    }
    const sessionId = decodeURIComponent(match[1]);
    (async () => {
      try {
        const { data } = await api.post("/auth/emergent/session", { session_id: sessionId });
        setUser(data);
        // clear the hash
        window.history.replaceState({}, "", window.location.pathname);
        navigate(data.role === "admin" ? "/admin" : "/dashboard", { replace: true, state: { user: data } });
      } catch {
        navigate("/login", { replace: true });
      }
    })();
  }, [location.hash, navigate, setUser]);

  return (
    <div className="min-h-screen grid place-items-center bg-[#0a0a0a] text-white/60" data-testid="auth-callback">
      <div className="font-mono-accent">Signing you in…</div>
    </div>
  );
}
