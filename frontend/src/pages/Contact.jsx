import { useState } from "react";
import { toast } from "sonner";
import Navbar from "@/components/layout/Navbar";
import Footer from "@/components/layout/Footer";
import { api, formatApiErrorDetail } from "@/lib/api";
import { Mail, MessageSquare, Send } from "lucide-react";
import { Helmet } from "react-helmet-async";

export default function Contact() {
  const [form, setForm] = useState({ name: "", email: "", subject: "", message: "" });
  const [busy, setBusy] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    setBusy(true);
    try {
      await api.post("/contact", form);
      toast.success("Message sent. We'll reply within 24 hours.");
      setForm({ name: "", email: "", subject: "", message: "" });
    } catch (err) {
      toast.error(formatApiErrorDetail(err.response?.data?.detail) || "Failed to send.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <>
      <Helmet>
        <div className="min-h-screen bg-[#0a0a0a] text-white" data-testid="contact-page">
          <Navbar />

          <section className="max-w-7xl mx-auto px-6 py-20 md:py-28 grid lg:grid-cols-2 gap-16">
            <div>
              <p className="overline mb-4">Contact</p>
              <h1 className="font-heading text-5xl md:text-6xl font-extrabold tracking-tighter">
                Let’s talk about your project.
              </h1>
              <p className="mt-6 text-lg text-white/70 leading-relaxed max-w-lg">
                Send a message and you’ll hear back — no bots, no funnels, no “we’ll circle back”.
              </p>

              <div className="mt-10 space-y-6">
                <div className="flex items-start gap-4">
                  <div className="w-11 h-11 grid place-items-center bg-[#085DD4]/10 border border-[#085DD4]/40 shrink-0">
                    <Mail className="w-5 h-5 text-[#085DD4]" />
                  </div>
                  <div>
                    <p className="overline mb-1">Email</p>
                    <a href="mailto:labostechnologies.india@gmail.com" className="text-white hover:text-[#085DD4]">labostechnologies.india@gmail.com</a>
                  </div>
                </div>
                <div className="flex items-start gap-4">
                  <div className="w-11 h-11 grid place-items-center bg-[#085DD4]/10 border border-[#085DD4]/40 shrink-0">
                    <MessageSquare className="w-5 h-5 text-[#085DD4]" />
                  </div>
                  <div>
                    <p className="overline mb-1">Response Time</p>
                    <p className="text-white">Under 24 hours, Mon–Fri.</p>
                  </div>
                </div>
              </div>
            </div>

            <form
              onSubmit={submit}
              className="bg-[#141414] border border-white/10 p-8 md:p-10 space-y-5"
              data-testid="contact-form"
            >
              <div>
                <label className="overline">Name</label>
                <input
                  required
                  value={form.name}
                  onChange={(e) => setForm({ ...form, name: e.target.value })}
                  className="mt-2 w-full bg-black/50 border border-white/15 focus:border-[#085DD4] p-3 text-white"
                  data-testid="contact-input-name"
                />
              </div>
              <div>
                <label className="overline">Email</label>
                <input
                  required
                  type="email"
                  value={form.email}
                  onChange={(e) => setForm({ ...form, email: e.target.value })}
                  className="mt-2 w-full bg-black/50 border border-white/15 focus:border-[#085DD4] p-3 text-white"
                  data-testid="contact-input-email"
                />
              </div>
              <div>
                <label className="overline">Subject</label>
                <input
                  required
                  value={form.subject}
                  onChange={(e) => setForm({ ...form, subject: e.target.value })}
                  className="mt-2 w-full bg-black/50 border border-white/15 focus:border-[#085DD4] p-3 text-white"
                  data-testid="contact-input-subject"
                />
              </div>
              <div>
                <label className="overline">Message</label>
                <textarea
                  required
                  rows={5}
                  value={form.message}
                  onChange={(e) => setForm({ ...form, message: e.target.value })}
                  className="mt-2 w-full bg-black/50 border border-white/15 focus:border-[#085DD4] p-3 text-white resize-none"
                  data-testid="contact-input-message"
                />
              </div>
              <button
                type="submit"
                disabled={busy}
                className="btn-primary w-full justify-center disabled:opacity-50"
                data-testid="contact-submit-btn"
              >
                {busy ? "Sending…" : (<>Send Message <Send className="w-4 h-4" /></>)}
              </button>
            </form>
          </section>

          <Footer />
        </div>
      </Helmet>
    </>
  );
}
