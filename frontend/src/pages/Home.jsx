import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import Navbar from "@/components/layout/Navbar";
import Footer from "@/components/layout/Footer";
import { ArrowRight, Code2, Wrench, Layers, Zap, ShieldCheck, Rocket } from "lucide-react";


const stats = [
  { k: "1", v: "Projects Shipped" },
  { k: "0", v: "Active Retainers" },
  { k: "99.9%", v: "Uptime Managed" },
  { k: "24h", v: "Response SLA" },
];

const services = [
  {
    icon: Code2,
    slug: "website-building",
    title: "Website Building",
    desc: "Landing pages, marketing sites, portfolios — built pixel-perfect and blazing fast.",
    image:
      "https://images.unsplash.com/photo-1760548425425-e42e77fa38f1?crop=entropy&cs=srgb&fm=jpg&ixid=M3w4NjA1OTN8MHwxfHNlYXJjaHwxfHx3ZWIlMjBkZXZlbG9wZXIlMjBjb2RpbmclMjBkYXJrJTIwbW9kZXJufGVufDB8fHx8MTc4NzU4MTgwN3ww&ixlib=rb-4.1.0&q=85",
  },
  {
    icon: Wrench,
    slug: "site-maintenance",
    title: "Site Maintenance",
    desc: "Uptime, backups, patching, content updates — your site stays healthy while you focus.",
    image:
      "https://images.pexels.com/photos/37730211/pexels-photo-37730211.jpeg?auto=compress&cs=tinysrgb&dpr=2&h=650&w=940",
  },
  {
    icon: Layers,
    slug: "application-building",
    title: "Application Building",
    desc: "Full-stack SaaS, portals & internal tools. Auth, payments, integrations included.",
    image:
      "https://images.pexels.com/photos/20694602/pexels-photo-20694602.png?auto=compress&cs=tinysrgb&dpr=2&h=650&w=940",
  },
];

const capabilities = [
  { icon: Zap, title: "Fast Delivery", desc: "Ship in weeks, not months. Focused scope, sharp execution." },
  { icon: ShieldCheck, title: "Secure by Default", desc: "Auth, HTTPS, backups, and hardened defaults from day one." },
  { icon: Rocket, title: "Growth-Ready", desc: "Scalable stacks (React, FastAPI, Mongo) that grow with you." },
];

export default function Home() {
  return (
    <div className="min-h-screen bg-[#0a0a0a] text-white" data-testid="home-page">
      <Navbar />

      {/* HERO */}
      <section className="relative overflow-hidden">
        <div
          className="hero-bg absolute inset-0 bg-cover bg-center opacity-40"
          style={{
            backgroundImage:
              "url(https://images.unsplash.com/photo-1638184984605-af1f05249a56?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NDk1Nzh8MHwxfHNlYXJjaHw0fHxhYnN0cmFjdCUyMGRhcmslMjB0ZWNobm9sb2d5JTIwYmFja2dyb3VuZHxlbnwwfHx8fDE3ODc1ODE4MDd8MA&ixlib=rb-4.1.0&q=85)",
          }}
        />
        <div className="absolute inset-0 bg-gradient-to-b from-black/70 via-black/60 to-black" />
        <div className="relative max-w-7xl mx-auto px-6 py-32 md:py-44">
          <motion.p
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="overline mb-6"
          >
            LABOS TECHNOLOGIES | IT STUDIO
          </motion.p>
          <motion.h1
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="font-heading text-5xl md:text-7xl lg:text-8xl font-extrabold leading-[0.95] tracking-tighter max-w-5xl"
          >
            Websites, Apps & <br />
            <span className="text-[#085DD4]">Uptime</span> — engineered by one focused human.
          </motion.h1>
          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.25 }}
            className="mt-8 text-lg md:text-xl text-white/70 max-w-2xl leading-relaxed"
          >
            LABOS is a virtual IT studio for founders who want senior-level craft without
            the agency drag. Book a package, request a custom quote, or hire us to keep your stack alive.
          </motion.p>
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
            className="mt-10 flex flex-wrap gap-4"
          >
            <Link to="/services" data-testid="hero-explore-services-btn" className="btn-primary">
              Explore Services <ArrowRight className="w-4 h-4" />
            </Link>
            <Link to="/contact" data-testid="hero-request-quote-btn" className="btn-outline">
              Request a Quote
            </Link>
          </motion.div>
        </div>
      </section>

      {/* STATS */}
      <section className="border-y border-white/10 bg-[#0d0d0d]">
        <div className="max-w-7xl mx-auto px-6 py-16 grid grid-cols-2 md:grid-cols-4 gap-8">
          {stats.map((s) => (
            <div key={s.v} data-testid={`stat-${s.v.toLowerCase().replace(/\s/g, "-")}`}>
              <p className="font-heading text-4xl md:text-5xl font-extrabold text-[#085DD4]">{s.k}</p>
              <p className="text-sm text-white/60 mt-2">{s.v}</p>
            </div>
          ))}
        </div>
      </section>

      {/* SERVICES BENTO */}
      <section className="max-w-7xl mx-auto px-6 py-28">
        <div className="flex items-end justify-between mb-14 flex-wrap gap-6">
          <div>
            <p className="overline mb-3">Services</p>
            <h2 className="font-heading text-4xl md:text-5xl font-bold tracking-tighter max-w-2xl">
              How LABOS helps you ship.
            </h2>
          </div>
          <Link to="/services" className="btn-outline text-sm" data-testid="services-see-all-btn">
            See all packages <ArrowRight className="w-4 h-4" />
          </Link>
        </div>

        <div className="grid md:grid-cols-3 gap-6">
          {services.map((s, i) => (
            <motion.div
              key={s.slug}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.08 }}
              className="card-lift group relative bg-[#141414] border border-white/10 overflow-hidden"
              data-testid={`home-service-card-${s.slug}`}
            >
              <div className="aspect-[4/3] overflow-hidden">
                <img
                  src={s.image}
                  alt={s.title}
                  className="w-full h-full object-cover opacity-70 group-hover:opacity-90 group-hover:scale-105 transition-all duration-500"
                />
              </div>
              <div className="p-7">
                <s.icon className="w-6 h-6 text-[#085DD4] mb-4" />
                <h3 className="font-heading text-2xl font-semibold mb-2">{s.title}</h3>
                <p className="text-white/60 text-sm leading-relaxed">{s.desc}</p>
                <Link
                  to="/services"
                  className="inline-flex items-center gap-1 mt-6 text-[#085DD4] font-semibold text-sm hover:gap-2 transition-all"
                >
                  Learn more <ArrowRight className="w-4 h-4" />
                </Link>
              </div>
            </motion.div>
          ))}
        </div>
      </section>

      {/* CAPABILITIES */}
      <section className="bg-[#0d0d0d] border-t border-white/10">
        <div className="max-w-7xl mx-auto px-6 py-28">
          <p className="overline mb-3">Why LABOS</p>
          <h2 className="font-heading text-4xl md:text-5xl font-bold tracking-tighter max-w-3xl mb-14">
            Boutique focus. Enterprise-grade craft.
          </h2>
          <div className="grid md:grid-cols-3 gap-6">
            {capabilities.map((c) => (
              <div key={c.title} className="bg-[#141414] border border-white/10 p-8">
                <c.icon className="w-8 h-8 text-[#085DD4] mb-5" />
                <h3 className="font-heading text-xl font-semibold mb-2">{c.title}</h3>
                <p className="text-white/60 text-sm leading-relaxed">{c.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="max-w-7xl mx-auto px-6 py-28">
        <div className="border border-[#085DD4]/40 bg-gradient-to-br from-[#00113a] to-[#0a0a0a] p-12 md:p-20 text-center">
          <p className="overline mb-4">Ready when you are</p>
          <h2 className="font-heading text-4xl md:text-6xl font-extrabold tracking-tighter max-w-3xl mx-auto">
            Let’s build something that ships.
          </h2>
          <p className="text-white/70 mt-6 max-w-xl mx-auto">
            Pick a package or send us your requirements — you’ll hear back within 24 hours.
          </p>
          <div className="mt-10 flex flex-wrap gap-4 justify-center">
            <Link to="/services" className="btn-primary" data-testid="cta-book-service-btn">
              Book a Service <ArrowRight className="w-4 h-4" />
            </Link>
            <Link to="/contact" className="btn-outline" data-testid="cta-contact-btn">
              Get in Touch
            </Link>
          </div>
        </div>
      </section>

      <Footer />
    </div>
  );
}
