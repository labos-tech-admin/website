import { useState } from "react";
import { Link, useNavigate, useLocation } from "react-router-dom";
import { toast } from "sonner";
import Navbar from "@/components/layout/Navbar";
import Footer from "@/components/layout/Footer";
import { useAuth } from "@/context/AuthContext";
import { formatApiErrorDetail } from "@/lib/api";

export default function Login() {
  const [form, setForm] = useState({ email: "", password: "" });
  const [busy, setBusy] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const submit = async (e) => {
    e.preventDefault();
    setBusy(true);
    try {
      const user = await login(form.email, form.password);
      toast.success("Welcome back!");
      const to = user.role === "admin" ? "/admin" : (location.state?.from?.pathname || "/dashboard");
      navigate(to);
    } catch (err) {
      const detail = err.response?.data?.detail;
      // Detect email_not_verified structured error and route to verification page
      if (detail && typeof detail === "object" && detail.code === "email_not_verified") {
        toast.message("Please verify your email to continue.");
        navigate(`/verify-otp?email=${encodeURIComponent(detail.email || form.email)}`);
        return;
      }
      toast.error(formatApiErrorDetail(detail) || "Login failed.");
    } finally {
      setBusy(false);
    }
  };

  const googleLogin = () => {
    // REMINDER: DO NOT HARDCODE THE URL, OR ADD ANY FALLBACKS OR REDIRECT URLS, THIS BREAKS THE AUTH
    const redirectUrl = window.location.origin + "/dashboard";
    window.location.href = `https://auth.emergentagent.com/?redirect=${encodeURIComponent(redirectUrl)}`;
  };

  return (
    <div className="min-h-screen bg-[#0a0a0a] text-white flex flex-col" data-testid="login-page">
      <Navbar />
      <div className="flex-1 grid place-items-center px-6 py-16">
        <div className="w-full max-w-md">
          <p className="overline mb-3">Welcome back</p>
          <h1 className="font-heading text-4xl font-extrabold tracking-tighter mb-8">Sign in to LABOS</h1>
          <form onSubmit={submit} className="bg-[#141414] border border-white/10 p-8 space-y-5">
            <div>
              <label className="overline">Email</label>
              <input
                required
                type="email"
                value={form.email}
                onChange={(e) => setForm({ ...form, email: e.target.value })}
                className="mt-2 w-full bg-black/50 border border-white/15 focus:border-[#085DD4] p-3"
                data-testid="login-input-email"
              />
            </div>
            <div>
              <label className="overline">Password</label>
              <input
                required
                type="password"
                value={form.password}
                onChange={(e) => setForm({ ...form, password: e.target.value })}
                className="mt-2 w-full bg-black/50 border border-white/15 focus:border-[#085DD4] p-3"
                data-testid="login-input-password"
              />
            </div>
            <button type="submit" disabled={busy} className="btn-primary w-full justify-center disabled:opacity-50" data-testid="login-submit-btn">
              {busy ? "Signing in…" : "Sign In"}
            </button>
          </form>

          <div className="flex items-center gap-3 my-6">
            <div className="h-px bg-white/10 flex-1" />
            <span className="text-xs text-white/40 font-mono-accent">OR</span>
            <div className="h-px bg-white/10 flex-1" />
          </div>

          <button
            onClick={googleLogin}
            className="w-full border border-white/20 hover:border-[#085DD4] hover:text-[#085DD4] py-3 font-heading font-semibold flex items-center justify-center gap-2 transition-colors"
            data-testid="login-google-btn"
          >
            <svg className="w-5 h-5" viewBox="0 0 24 24"><path fill="currentColor" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/><path fill="currentColor" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/><path fill="currentColor" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/><path fill="currentColor" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/></svg>
            Continue with Google
          </button>

          <p className="text-center text-sm text-white/60 mt-6">
            No account?{" "}
            <Link to="/register" className="text-[#085DD4] hover:underline" data-testid="login-register-link">
              Create one
            </Link>
          </p>
        </div>
      </div>
      <Footer />
    </div>
  );
}
