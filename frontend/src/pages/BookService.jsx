import { useEffect, useState } from "react";
import { useSearchParams, useNavigate } from "react-router-dom";
import { toast } from "sonner";
import Navbar from "@/components/layout/Navbar";
import Footer from "@/components/layout/Footer";
import { api, formatApiErrorDetail } from "@/lib/api";
import { payWithRazorpay } from "@/lib/razorpay";
import { ArrowRight, Check } from "lucide-react";

export default function BookService() {
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const serviceSlug = params.get("service");
  const packageId = params.get("package");
  const forceQuote = params.get("type") === "quote";

  const [service, setService] = useState(null);
  const [selectedPackage, setSelectedPackage] = useState(null);
  const [bookingType, setBookingType] = useState(forceQuote || !packageId ? "quote" : "package");
  const [busy, setBusy] = useState(false);
  const [form, setForm] = useState({
    project_title: "",
    requirements: "",
    budget: "",
    timeline: "",
    contact_phone: "",
  });

  useEffect(() => {
    if (!serviceSlug) {
      navigate("/services");
      return;
    }
    api.get(`/services/${serviceSlug}`).then(({ data }) => {
      setService(data);
      if (packageId) {
        const p = data.packages.find((x) => x.package_id === packageId);
        if (p) {
          setSelectedPackage(p);
          setForm((f) => ({ ...f, project_title: `${data.title} — ${p.name}` }));
        }
      }
    }).catch(() => navigate("/services"));
  }, [serviceSlug, packageId, navigate]);

  const submit = async (e) => {
    e.preventDefault();
    setBusy(true);
    try {
      const payload = {
        service_slug: serviceSlug,
        booking_type: bookingType,
        package_id: bookingType === "package" ? selectedPackage?.package_id : null,
        project_title: form.project_title,
        requirements: form.requirements,
        budget: form.budget ? parseFloat(form.budget) : null,
        timeline: form.timeline || null,
        contact_phone: form.contact_phone || null,
      };
      const { data: booking } = await api.post("/bookings", payload);
      toast.success("Booking submitted!");
      if (bookingType === "package" && booking.amount) {
        // Open Razorpay modal immediately
        try {
          await payWithRazorpay(booking.booking_id);
          toast.success("Payment successful!");
          navigate("/payment/success?booking=" + booking.booking_id);
        } catch (err) {
          const msg = err?.response?.data?.detail || err?.message || "Payment cancelled";
          toast.error(msg);
          navigate("/dashboard");
        }
      } else {
        navigate("/dashboard");
      }
    } catch (err) {
      toast.error(formatApiErrorDetail(err.response?.data?.detail) || "Failed to submit booking.");
    } finally {
      setBusy(false);
    }
  };

  if (!service) {
    return (
      <div className="min-h-screen bg-[#0a0a0a] text-white/60 grid place-items-center">
        <div className="font-mono-accent">Loading…</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#0a0a0a] text-white" data-testid="book-service-page">
      <Navbar />
      <div className="max-w-5xl mx-auto px-6 py-16">
        <p className="overline mb-3">Book a service</p>
        <h1 className="font-heading text-4xl md:text-5xl font-extrabold tracking-tighter mb-3">
          {service.title}
        </h1>
        <p className="text-white/70 mb-10 max-w-2xl">{service.tagline}</p>

        <div className="grid lg:grid-cols-3 gap-8">
          <form onSubmit={submit} className="lg:col-span-2 bg-[#141414] border border-white/10 p-8 space-y-5" data-testid="booking-form">
            <div className="flex gap-3">
              <button
                type="button"
                onClick={() => setBookingType("package")}
                disabled={!selectedPackage}
                className={`px-4 py-2 border transition-colors ${
                  bookingType === "package"
                    ? "bg-[#FF7A00] text-black border-[#FF7A00]"
                    : "border-white/15 text-white/70 hover:border-white/40"
                } ${!selectedPackage ? "opacity-40 cursor-not-allowed" : ""}`}
                data-testid="tab-package"
              >
                Package
              </button>
              <button
                type="button"
                onClick={() => setBookingType("quote")}
                className={`px-4 py-2 border transition-colors ${
                  bookingType === "quote"
                    ? "bg-[#FF7A00] text-black border-[#FF7A00]"
                    : "border-white/15 text-white/70 hover:border-white/40"
                }`}
                data-testid="tab-quote"
              >
                Custom Quote
              </button>
            </div>

            <div>
              <label className="overline">Project Title</label>
              <input
                required
                value={form.project_title}
                onChange={(e) => setForm({ ...form, project_title: e.target.value })}
                className="mt-2 w-full bg-black/50 border border-white/15 focus:border-[#FF7A00] p-3"
                data-testid="booking-input-title"
              />
            </div>
            <div>
              <label className="overline">Requirements</label>
              <textarea
                required
                rows={6}
                value={form.requirements}
                onChange={(e) => setForm({ ...form, requirements: e.target.value })}
                placeholder="Tell us what you need — goals, features, references, deadlines."
                className="mt-2 w-full bg-black/50 border border-white/15 focus:border-[#FF7A00] p-3 resize-none"
                data-testid="booking-input-requirements"
              />
            </div>
            {bookingType === "quote" && (
              <div className="grid md:grid-cols-2 gap-4">
                <div>
                  <label className="overline">Budget (INR)</label>
                  <input
                    type="number"
                    min="0"
                    step="100"
                    value={form.budget}
                    onChange={(e) => setForm({ ...form, budget: e.target.value })}
                    className="mt-2 w-full bg-black/50 border border-white/15 focus:border-[#FF7A00] p-3"
                    data-testid="booking-input-budget"
                  />
                </div>
                <div>
                  <label className="overline">Timeline</label>
                  <input
                    placeholder="e.g. 4 weeks"
                    value={form.timeline}
                    onChange={(e) => setForm({ ...form, timeline: e.target.value })}
                    className="mt-2 w-full bg-black/50 border border-white/15 focus:border-[#FF7A00] p-3"
                    data-testid="booking-input-timeline"
                  />
                </div>
              </div>
            )}
            <div>
              <label className="overline">Phone (optional)</label>
              <input
                value={form.contact_phone}
                onChange={(e) => setForm({ ...form, contact_phone: e.target.value })}
                className="mt-2 w-full bg-black/50 border border-white/15 focus:border-[#FF7A00] p-3"
                data-testid="booking-input-phone"
              />
            </div>

            <button type="submit" disabled={busy} className="btn-primary w-full justify-center disabled:opacity-50" data-testid="booking-submit-btn">
              {busy ? "Submitting…" : bookingType === "package" ? (<>Continue to Payment <ArrowRight className="w-4 h-4" /></>) : "Submit Quote Request"}
            </button>
          </form>

          <aside className="bg-[#141414] border border-white/10 p-6 h-fit">
            {bookingType === "package" && selectedPackage ? (
              <>
                <p className="overline mb-2">Order Summary</p>
                <h3 className="font-heading text-xl font-bold">{selectedPackage.name}</h3>
                <p className="text-white/60 text-sm mt-1 mb-4">{selectedPackage.description}</p>
                <p className="font-heading text-3xl font-extrabold text-[#FF7A00] mb-4">
                  ₹{selectedPackage.amount.toLocaleString("en-IN")}
                </p>
                <ul className="space-y-2">
                  {selectedPackage.highlights.map((h) => (
                    <li key={h} className="flex items-start gap-2 text-sm text-white/80">
                      <Check className="w-4 h-4 text-[#FF7A00] mt-0.5 shrink-0" /> {h}
                    </li>
                  ))}
                </ul>
                <p className="text-xs text-white/50 mt-6">
                  You'll be charged via Razorpay. Test card: <code className="text-[#FF7A00]">4111 1111 1111 1111</code>
                </p>
              </>
            ) : (
              <>
                <p className="overline mb-2">How Custom Quotes Work</p>
                <ul className="space-y-3 text-sm text-white/70">
                  <li className="flex gap-2"><Check className="w-4 h-4 text-[#FF7A00] mt-0.5 shrink-0" /> Submit your requirements</li>
                  <li className="flex gap-2"><Check className="w-4 h-4 text-[#FF7A00] mt-0.5 shrink-0" /> Get a quote within 24 hrs</li>
                  <li className="flex gap-2"><Check className="w-4 h-4 text-[#FF7A00] mt-0.5 shrink-0" /> Approve & pay via Razorpay</li>
                  <li className="flex gap-2"><Check className="w-4 h-4 text-[#FF7A00] mt-0.5 shrink-0" /> Track progress on your dashboard</li>
                </ul>
              </>
            )}
          </aside>
        </div>
      </div>
      <Footer />
    </div>
  );
}
