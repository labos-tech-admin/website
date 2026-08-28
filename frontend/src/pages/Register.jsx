import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { toast } from "sonner";
import Navbar from "@/components/layout/Navbar";
import Footer from "@/components/layout/Footer";
import { useAuth } from "@/context/AuthContext";
import { formatApiErrorDetail } from "@/lib/api";

export default function Register() {
  const [form, setForm] = useState({ name: "", email: "", password: "" });
  const [busy, setBusy] = useState(false);
  const { register } = useAuth();
  const navigate = useNavigate();

  const submit = async (e) => {
    e.preventDefault();
    setBusy(true);
    try {
      const data = await register(form.email, form.password, form.name);
      if (data?.email_sent) {
        toast.success("Account created! Check your email for the verification code.");
      } else {
        toast.message("Account created. Enter the code you'll receive by email, or tap Resend.");
      }
      navigate(`/verify-otp?email=${encodeURIComponent(form.email)}`);
    } catch (err) {
      toast.error(formatApiErrorDetail(err.response?.data?.detail) || "Registration failed.");
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
    <div className="min-h-screen bg-[#0a0a0a] text-white flex flex-col" data-testid="register-page">
      <Navbar />
      <div className="flex-1 grid place-items-center px-6 py-16">
        <div className="w-full max-w-md">
          <p className="overline mb-3">Get started</p>
          <h1 className="font-heading text-4xl font-extrabold tracking-tighter mb-8">Create your LABOS account</h1>
          <form onSubmit={submit} className="bg-[#141414] border border-white/10 p-8 space-y-5">
            <div>
              <label className="overline">Full Name</label>
              <input
                required
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                className="mt-2 w-full bg-black/50 border border-white/15 focus:border-[#FF7A00] p-3"
                data-testid="register-input-name"
              />
            </div>
            <div>
              <label className="overline">Email</label>
              <input
                required
                type="email"
                value={form.email}
                onChange={(e) => setForm({ ...form, email: e.target.value })}
                className="mt-2 w-full bg-black/50 border border-white/15 focus:border-[#FF7A00] p-3"
                data-testid="register-input-email"
              />
            </div>
            <div>
              <label className="overline">Password</label>
              <input
                required
                type="password"
                minLength={6}
                value={form.password}
                onChange={(e) => setForm({ ...form, password: e.target.value })}
                className="mt-2 w-full bg-black/50 border border-white/15 focus:border-[#FF7A00] p-3"
                data-testid="register-input-password"
              />
            </div>
            <button type="submit" disabled={busy} className="btn-primary w-full justify-center disabled:opacity-50" data-testid="register-submit-btn">
              {busy ? "Creating…" : "Create Account"}
            </button>
          </form>

          <div className="flex items-center gap-3 my-6">
            <div className="h-px bg-white/10 flex-1" />
            <span className="text-xs text-white/40 font-mono-accent">OR</span>
            <div className="h-px bg-white/10 flex-1" />
          </div>

          <button
            onClick={googleLogin}
            className="w-full border border-white/20 hover:border-[#FF7A00] hover:text-[#FF7A00] py-3 font-heading font-semibold flex items-center justify-center gap-2 transition-colors"
            data-testid="register-google-btn"
          >
            Continue with Google
          </button>

          <p className="text-center text-sm text-white/60 mt-6">
            Already have an account?{" "}
            <Link to="/login" className="text-[#FF7A00] hover:underline" data-testid="register-login-link">
              Sign in
            </Link>
          </p>
        </div>
      </div>
      <Footer />
    </div>
  );
}
