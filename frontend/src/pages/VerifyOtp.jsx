import { useEffect, useMemo, useRef, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { toast } from "sonner";
import Navbar from "@/components/layout/Navbar";
import Footer from "@/components/layout/Footer";
import { useAuth } from "@/context/AuthContext";
import { formatApiErrorDetail } from "@/lib/api";
import { Mail, RotateCcw } from "lucide-react";

const LENGTH = 6;

export default function VerifyOtp() {
  const [params] = useSearchParams();
  const email = useMemo(() => params.get("email") || "", [params]);
  const navigate = useNavigate();
  const { verifyOtp, resendOtp } = useAuth();

  const [digits, setDigits] = useState(Array(LENGTH).fill(""));
  const [busy, setBusy] = useState(false);
  const [resendCooldown, setResendCooldown] = useState(0);
  const inputsRef = useRef([]);

  useEffect(() => {
    if (!email) {
      navigate("/register", { replace: true });
      return;
    }
    inputsRef.current[0]?.focus();
  }, [email, navigate]);

  useEffect(() => {
    if (resendCooldown <= 0) return;
    const t = setTimeout(() => setResendCooldown((s) => s - 1), 1000);
    return () => clearTimeout(t);
  }, [resendCooldown]);

  const setDigit = (i, val) => {
    const clean = val.replace(/\D/g, "").slice(0, 1);
    setDigits((prev) => {
      const next = [...prev];
      next[i] = clean;
      return next;
    });
    if (clean && i < LENGTH - 1) inputsRef.current[i + 1]?.focus();
  };

  const onKeyDown = (i, e) => {
    if (e.key === "Backspace" && !digits[i] && i > 0) {
      inputsRef.current[i - 1]?.focus();
    }
  };

  const onPaste = (e) => {
    const text = e.clipboardData.getData("text").replace(/\D/g, "").slice(0, LENGTH);
    if (!text) return;
    e.preventDefault();
    const arr = text.split("").concat(Array(LENGTH).fill("")).slice(0, LENGTH);
    setDigits(arr);
    inputsRef.current[Math.min(text.length, LENGTH - 1)]?.focus();
  };

  const submit = async (e) => {
    e?.preventDefault();
    const code = digits.join("");
    if (code.length !== LENGTH) {
      toast.error("Enter all 6 digits");
      return;
    }
    setBusy(true);
    try {
      const user = await verifyOtp(email, code);
      toast.success("Email verified — welcome to LABOS!");
      navigate(user.role === "admin" ? "/admin" : "/dashboard");
    } catch (err) {
      toast.error(formatApiErrorDetail(err.response?.data?.detail) || "Verification failed.");
      setDigits(Array(LENGTH).fill(""));
      inputsRef.current[0]?.focus();
    } finally {
      setBusy(false);
    }
  };

  const doResend = async () => {
    if (resendCooldown > 0) return;
    try {
      await resendOtp(email);
      toast.success("A new code is on its way.");
      setResendCooldown(60);
    } catch (err) {
      const detail = err.response?.data?.detail || "";
      const match = typeof detail === "string" && detail.match(/wait (\d+)s/i);
      if (match) setResendCooldown(parseInt(match[1], 10));
      toast.error(formatApiErrorDetail(detail) || "Couldn't resend the code.");
    }
  };

  return (
    <div className="min-h-screen bg-[#0a0a0a] text-white flex flex-col" data-testid="verify-otp-page">
      <Navbar />
      <div className="flex-1 grid place-items-center px-6 py-16">
        <div className="w-full max-w-md">
          <div className="flex justify-center mb-6">
            <div className="w-14 h-14 grid place-items-center bg-[#085DD4]/10 border border-[#085DD4]/40">
              <Mail className="w-6 h-6 text-[#085DD4]" />
            </div>
          </div>
          <p className="overline text-center mb-3">Verify your email</p>
          <h1 className="font-heading text-3xl font-extrabold tracking-tighter text-center mb-3">
            Enter the 6-digit code
          </h1>
          <p className="text-white/60 text-center mb-8 text-sm">
            We sent it to <span className="text-white font-medium">{email}</span>. It expires in 10 minutes.
          </p>

          <form onSubmit={submit} className="bg-[#141414] border border-white/10 p-8">
            <div className="flex gap-2 justify-center mb-6" onPaste={onPaste}>
              {digits.map((d, i) => (
                <input
                  key={i}
                  ref={(el) => (inputsRef.current[i] = el)}
                  type="text"
                  inputMode="numeric"
                  maxLength={1}
                  value={d}
                  onChange={(e) => setDigit(i, e.target.value)}
                  onKeyDown={(e) => onKeyDown(i, e)}
                  data-testid={`otp-input-${i}`}
                  className="w-12 h-14 md:w-14 md:h-16 text-center text-2xl md:text-3xl font-heading font-bold bg-black/50 border border-white/15 focus:border-[#085DD4] outline-none"
                />
              ))}
            </div>
            <button
              type="submit"
              disabled={busy}
              className="btn-primary w-full justify-center disabled:opacity-50"
              data-testid="verify-submit-btn"
            >
              {busy ? "Verifying…" : "Verify & Continue"}
            </button>
          </form>

          <div className="flex flex-col items-center gap-3 mt-6">
            <button
              onClick={doResend}
              disabled={resendCooldown > 0}
              className="text-sm text-white/60 hover:text-[#085DD4] transition-colors flex items-center gap-2 disabled:opacity-40 disabled:cursor-not-allowed"
              data-testid="resend-otp-btn"
            >
              <RotateCcw className="w-4 h-4" />
              {resendCooldown > 0 ? `Resend in ${resendCooldown}s` : "Resend code"}
            </button>
            <Link to="/register" className="text-sm text-white/40 hover:text-white/70" data-testid="verify-back-link">
              Use a different email
            </Link>
          </div>
        </div>
      </div>
      <Footer />
    </div>
  );
}
