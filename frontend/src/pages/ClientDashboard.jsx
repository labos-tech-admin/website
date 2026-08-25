import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { toast } from "sonner";
import Navbar from "@/components/layout/Navbar";
import Footer from "@/components/layout/Footer";
import { useAuth } from "@/context/AuthContext";
import { api, formatApiErrorDetail } from "@/lib/api";
import { payWithRazorpay } from "@/lib/razorpay";
import { CreditCard, Plus, Clock } from "lucide-react";

const statusColor = {
  new: "bg-blue-500/10 text-blue-400 border-blue-500/30",
  quoted: "bg-purple-500/10 text-purple-400 border-purple-500/30",
  in_progress: "bg-[#FF7A00]/10 text-[#FF7A00] border-[#FF7A00]/40",
  completed: "bg-green-500/10 text-green-400 border-green-500/30",
  cancelled: "bg-red-500/10 text-red-400 border-red-500/30",
};

const paymentColor = {
  unpaid: "text-white/60",
  pending: "text-yellow-400",
  paid: "text-green-400",
  refunded: "text-blue-400",
};

export default function ClientDashboard() {
  const { user } = useAuth();
  const [bookings, setBookings] = useState([]);
  const [loading, setLoading] = useState(true);

  const load = async () => {
    try {
      const { data } = await api.get("/bookings/mine");
      setBookings(data);
    } catch (err) {
      toast.error("Failed to load bookings.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const pay = async (booking) => {
    try {
      await payWithRazorpay(booking.booking_id);
      toast.success("Payment successful!");
      await load();
    } catch (err) {
      const msg = err?.response?.data?.detail || err?.message || "Payment cancelled";
      toast.error(msg);
    }
  };

  return (
    <div className="min-h-screen bg-[#0a0a0a] text-white" data-testid="client-dashboard">
      <Navbar />
      <div className="max-w-7xl mx-auto px-6 py-14">
        <div className="flex items-end justify-between gap-6 flex-wrap mb-10">
          <div>
            <p className="overline mb-2">Client Portal</p>
            <h1 className="font-heading text-4xl md:text-5xl font-extrabold tracking-tighter">
              Welcome, {user?.name?.split(" ")[0] || "there"}.
            </h1>
            <p className="text-white/60 mt-2">Track your bookings, quotes and payments.</p>
          </div>
          <Link to="/services" className="btn-primary" data-testid="dashboard-new-booking-btn">
            <Plus className="w-4 h-4" /> New Booking
          </Link>
        </div>

        {loading ? (
          <div className="text-white/60">Loading…</div>
        ) : bookings.length === 0 ? (
          <div className="border border-dashed border-white/15 p-16 text-center" data-testid="dashboard-empty-state">
            <Clock className="w-10 h-10 text-white/30 mx-auto mb-4" />
            <h3 className="font-heading text-2xl font-bold mb-2">No bookings yet</h3>
            <p className="text-white/60 mb-6">Start by exploring our services.</p>
            <Link to="/services" className="btn-primary">Browse Services</Link>
          </div>
        ) : (
          <div className="grid gap-4">
            {bookings.map((b) => (
              <div key={b.booking_id} className="bg-[#141414] border border-white/10 p-6" data-testid={`booking-row-${b.booking_id}`}>
                <div className="flex flex-wrap items-start justify-between gap-4 mb-4">
                  <div>
                    <p className="overline mb-1">{b.service_title}{b.package_name ? ` · ${b.package_name}` : " · Custom Quote"}</p>
                    <h3 className="font-heading text-xl font-bold">{b.project_title}</h3>
                  </div>
                  <div className="flex flex-col items-end gap-2">
                    <span className={`text-xs font-mono-accent px-3 py-1 border ${statusColor[b.status] || ""}`}>
                      {b.status.replace("_", " ")}
                    </span>
                    <span className={`text-xs font-mono-accent ${paymentColor[b.payment_status]}`}>
                      Payment: {b.payment_status}
                    </span>
                  </div>
                </div>
                <p className="text-white/70 text-sm line-clamp-2 mb-4">{b.requirements}</p>
                <div className="flex flex-wrap items-center justify-between gap-4 pt-4 border-t border-white/10">
                  <div className="flex flex-wrap gap-6 text-sm">
                    {b.amount != null && (
                      <div><span className="text-white/50">Amount</span> <span className="text-[#FF7A00] font-bold">₹{b.amount.toLocaleString("en-IN")}</span></div>
                    )}
                    {b.timeline && <div><span className="text-white/50">Timeline</span> <span className="text-white">{b.timeline}</span></div>}
                    {b.budget && <div><span className="text-white/50">Budget</span> <span className="text-white">₹{b.budget.toLocaleString("en-IN")}</span></div>}
                  </div>
                  {b.amount && b.payment_status !== "paid" && (
                    <button
                      onClick={() => pay(b)}
                      className="btn-primary text-sm"
                      data-testid={`booking-pay-btn-${b.booking_id}`}
                    >
                      <CreditCard className="w-4 h-4" /> Pay ₹{b.amount.toLocaleString("en-IN")}
                    </button>
                  )}
                </div>
                {b.admin_notes && (
                  <div className="mt-4 p-3 bg-black/40 border-l-2 border-[#FF7A00] text-sm text-white/80">
                    <p className="overline mb-1 text-[10px]">Note from LABOS</p>
                    {b.admin_notes}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
      <Footer />
    </div>
  );
}
