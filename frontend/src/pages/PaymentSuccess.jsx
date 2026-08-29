import { Link } from "react-router-dom";
import Navbar from "@/components/layout/Navbar";
import Footer from "@/components/layout/Footer";
import { CheckCircle2 } from "lucide-react";

export default function PaymentSuccess() {
  return (
    <div className="min-h-screen bg-[#0a0a0a] text-white flex flex-col" data-testid="payment-success-page">
      <Navbar />
      <div className="flex-1 grid place-items-center px-6 py-16">
        <div className="max-w-lg text-center bg-[#141414] border border-white/10 p-12">
          <CheckCircle2 className="w-14 h-14 text-green-400 mx-auto mb-6" />
          <h1 className="font-heading text-3xl font-bold mb-2">Payment successful!</h1>
          <p className="text-white/70 mb-6">
            Your payment was received and your project has moved to{" "}
            <span className="text-[#085DD4] font-bold">In Progress</span>.
          </p>
          <Link to="/dashboard" className="btn-primary" data-testid="payment-back-to-dashboard-btn">
            Go to Dashboard
          </Link>
        </div>
      </div>
      <Footer />
    </div>
  );
}
