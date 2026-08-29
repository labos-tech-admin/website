import Navbar from "@/components/layout/Navbar";
import Footer from "@/components/layout/Footer";
import { Check } from "lucide-react";
import { Helmet } from "react-helmet-async";

const values = [
  { title: "Direct Line", desc: "You talk to the person doing the work. No account manager, no gatekeepers." },
  { title: "Ruthless Focus", desc: "One project at a time. Deep work over reactive multitasking." },
  { title: "Own the Stack", desc: "Full ownership from design, code, deployment, to keeping it alive." },
  { title: "Fair Pricing", desc: "Transparent packages. Custom quotes with no hidden markups." },
];

export default function About() {
  return (
    <>
      <Helmet>
        <div className="min-h-screen bg-[#0a0a0a] text-white" data-testid="about-page">
          <Navbar />

          <section className="max-w-7xl mx-auto px-6 py-24 md:py-32">
            <p className="overline mb-6">About LABOS</p>
            <h1 className="font-heading text-5xl md:text-7xl font-extrabold tracking-tighter max-w-4xl">
              A virtual IT studio built for founders in a hurry.
            </h1>
            <p className="mt-8 text-lg md:text-xl text-white/70 max-w-3xl leading-relaxed">
              LABOS Technologies is a one-person virtual company. That’s not a limitation — it’s the entire
              point. You get a senior engineer’s full attention, without agency overhead, offshore
              hand-offs, or endless discovery calls.
            </p>
          </section>

          <section className="border-y border-white/10 bg-[#0d0d0d]">
            <div className="max-w-7xl mx-auto px-6 py-24 grid md:grid-cols-2 gap-16 items-center">
              <div>
                <p className="overline mb-3">What we stand for</p>
                <h2 className="font-heading text-4xl md:text-5xl font-bold tracking-tighter mb-8">
                  Four principles. No exceptions.
                </h2>
                <div className="space-y-6">
                  {values.map((v) => (
                    <div key={v.title} className="flex gap-4">
                      <div className="mt-1 w-8 h-8 grid place-items-center bg-[#085DD4]/10 border border-[#085DD4]/40 shrink-0">
                        <Check className="w-4 h-4 text-[#085DD4]" />
                      </div>
                      <div>
                        <h3 className="font-heading text-lg font-semibold mb-1">{v.title}</h3>
                        <p className="text-white/60 text-sm leading-relaxed">{v.desc}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
              <div className="relative aspect-[4/5] overflow-hidden border border-white/10">
                <img
                  src="https://images.pexels.com/photos/13027585/pexels-photo-13027585.jpeg?auto=compress&cs=tinysrgb&dpr=2&h=650&w=940"
                  alt="LABOS studio"
                  className="w-full h-full object-cover"
                />
                <div className="absolute inset-0 bg-gradient-to-t from-black via-transparent to-transparent" />
                <div className="absolute bottom-6 left-6 right-6">
                  <p className="overline mb-2">Est. 2024</p>
                  <p className="font-heading text-2xl font-bold">Built to ship, not to bill hours.</p>
                </div>
              </div>
            </div>
          </section>

          <section className="max-w-4xl mx-auto px-6 py-24">
            <p className="overline mb-3">The stack</p>
            <h2 className="font-heading text-3xl md:text-4xl font-bold tracking-tighter mb-6">
              Modern, boring, and reliable.
            </h2>
            <p className="text-white/70 leading-relaxed">
              React, FastAPI, MongoDB, Stripe, and the boring-but-solid ops layer on top. We pick tools
              that will still be around and healthy in five years — not whatever’s trending on Twitter this week.
            </p>
          </section>

          <Footer />
        </div>
      </Helmet>
    </>
  );
}
