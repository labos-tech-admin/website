import { useEffect, useState, useRef } from "react";
import { useSearchParams, Link } from "react-router-dom";
import Navbar from "@/components/layout/Navbar";
import Footer from "@/components/layout/Footer";
import { api } from "@/lib/api";
import { CheckCircle2, Loader2, XCircle } from "lucide-react";

export default function PaymentSuccess() {
  const [params] = useSearchParams();
  const sessionId = params.get("session_id");
  const [status, setStatus] = useState("polling"); // polling | paid | failed
  const attempts = useRef(0);

  useEffect(() => {
    if (!sessionId) {
      setStatus("failed");
      return;
    }
    let timer;
    const poll = async () => {
      attempts.current += 1;
      try {
        const { data } = await api.get(`/payments/status/${sessionId}`);
        if (data.payment_status === "paid") {
          setStatus("paid");
          return;
        }
        if (["expired", "failed"].includes(data.payment_status) || attempts.current > 15) {
          setStatus("failed");
          return;
        }
      } catch { /* keep polling */ }
      timer = setTimeout(poll, 2000);
    };
    poll();
    return () => clearTimeout(timer);
  }, [sessionId]);

  return (
    <div className="min-h-screen bg-[#0a0a0a] text-white flex flex-col" data-testid="payment-success-page">
      <Navbar />
      <div className="flex-1 grid place-items-center px-6 py-16">
        <div className="max-w-lg text-center bg-[#141414] border border-white/10 p-12">
          {status === "polling" && (
            <>
              <Loader2 className="w-14 h-14 text-[#FF7A00] mx-auto animate-spin mb-6" />
              <h1 className="font-heading text-3xl font-bold mb-2">Confirming payment…</h1>
              <p className="text-white/60">Hang tight, this usually takes a couple of seconds.</p>
            </>
          )}
          {status === "paid" && (
            <>
              <CheckCircle2 className="w-14 h-14 text-green-400 mx-auto mb-6" />
              <h1 className="font-heading text-3xl font-bold mb-2">Payment successful!</h1>
              <p className="text-white/70 mb-6">
                We received your payment and your project has moved to <span className="text-[#FF7A00] font-bold">In Progress</span>.
              </p>
              <Link to="/dashboard" className="btn-primary" data-testid="payment-back-to-dashboard-btn">Go to Dashboard</Link>
            </>
          )}
          {status === "failed" && (
            <>
              <XCircle className="w-14 h-14 text-red-400 mx-auto mb-6" />
              <h1 className="font-heading text-3xl font-bold mb-2">Payment not confirmed</h1>
              <p className="text-white/70 mb-6">If you completed payment, refresh in a minute — otherwise try again from your dashboard.</p>
              <Link to="/dashboard" className="btn-outline">Back to Dashboard</Link>
            </>
          )}
        </div>
      </div>
      <Footer />
    </div>
  );
}
