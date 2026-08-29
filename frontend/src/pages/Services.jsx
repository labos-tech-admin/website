import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import Navbar from "@/components/layout/Navbar";
import Footer from "@/components/layout/Footer";
import { api } from "@/lib/api";
import { Check, ArrowRight } from "lucide-react";

export default function Services() {
  const [services, setServices] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get("/services")
      .then(({ data }) => setServices(data))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="min-h-screen bg-[#0a0a0a] text-white" data-testid="services-page">
      <Navbar />

      <section className="max-w-7xl mx-auto px-6 py-20 md:py-28">
        <p className="overline mb-4">Services</p>
        <h1 className="font-heading text-5xl md:text-7xl font-extrabold tracking-tighter max-w-4xl">
          Pick a package. Or bring us a puzzle.
        </h1>
        <p className="mt-6 text-lg text-white/70 max-w-2xl leading-relaxed">
          Fixed-price packages for common needs. Custom quotes for everything else. Everything
          delivered by one focused engineer.
        </p>
      </section>

      {loading ? (
        <div className="max-w-7xl mx-auto px-6 pb-24 text-white/60">Loading services…</div>
      ) : (
        services.map((svc, idx) => (
          <section
            key={svc.slug}
            className={`border-t border-white/10 ${idx % 2 === 1 ? "bg-[#0d0d0d]" : ""}`}
            data-testid={`service-section-${svc.slug}`}
          >
            <div className="max-w-7xl mx-auto px-6 py-20 grid lg:grid-cols-5 gap-12">
              <div className="lg:col-span-2">
                <div className="aspect-[4/3] overflow-hidden border border-white/10 mb-6">
                  <img src={svc.image} alt={svc.title} className="w-full h-full object-cover" />
                </div>
                <p className="overline mb-3">{svc.tagline}</p>
                <h2 className="font-heading text-3xl md:text-4xl font-bold tracking-tighter mb-4">
                  {svc.title}
                </h2>
                <p className="text-white/70 leading-relaxed">{svc.description}</p>
              </div>

              <div className="lg:col-span-3 grid md:grid-cols-2 gap-6 content-start">
                {svc.packages.map((p) => (
                  <div
                    key={p.package_id}
                    className="card-lift bg-[#141414] border border-white/10 p-7 flex flex-col"
                    data-testid={`package-card-${p.package_id}`}
                  >
                    <p className="overline mb-2">{svc.title}</p>
                    <h3 className="font-heading text-2xl font-bold">{p.name}</h3>
                    <p className="text-white/60 text-sm mt-1 mb-5">{p.description}</p>
                    <p className="font-heading text-4xl font-extrabold text-[#085DD4] mb-6">
                      ₹{p.amount.toLocaleString("en-IN")}
                      <span className="text-sm font-medium text-white/50 ml-2">
                        {p.package_id.includes("monthly") ? "/mo" : "one-time"}
                      </span>
                    </p>
                    <ul className="space-y-2 mb-8 flex-1">
                      {p.highlights.map((h) => (
                        <li key={h} className="flex items-start gap-2 text-sm text-white/80">
                          <Check className="w-4 h-4 text-[#085DD4] mt-0.5 shrink-0" /> {h}
                        </li>
                      ))}
                    </ul>
                    <Link
                      to={`/book?service=${svc.slug}&package=${p.package_id}`}
                      className="btn-primary text-sm justify-center"
                      data-testid={`book-package-btn-${p.package_id}`}
                    >
                      Book Package <ArrowRight className="w-4 h-4" />
                    </Link>
                  </div>
                ))}
                <div className="md:col-span-2 border border-dashed border-white/15 p-7 flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
                  <div>
                    <p className="overline mb-2">Something bigger?</p>
                    <h3 className="font-heading text-2xl font-bold">Request a custom quote</h3>
                    <p className="text-white/60 text-sm mt-1">
                      Tell us your scope, budget, and timeline. We reply within 24 hours.
                    </p>
                  </div>
                  <Link
                    to={`/book?service=${svc.slug}&type=quote`}
                    className="btn-outline shrink-0"
                    data-testid={`request-quote-btn-${svc.slug}`}
                  >
                    Request Quote <ArrowRight className="w-4 h-4" />
                  </Link>
                </div>
              </div>
            </div>
          </section>
        ))
      )}

      <Footer />
    </div>
  );
}
