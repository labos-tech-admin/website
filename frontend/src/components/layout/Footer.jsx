import { Link } from "react-router-dom";
import { Zap, Mail, Github, Linkedin } from "lucide-react";
import logo from "../../images/logo.png"

export default function Footer() {
  return (
    <footer className="border-t border-white/10 bg-black">
      <div className="max-w-7xl mx-auto px-6 py-16 grid md:grid-cols-4 gap-10">
        <div>
          <div className="flex items-center gap-2 mb-4">
            <span className="w-9 h-9 grid place-items-center">
              {/* <Zap className="w-5 h-5 text-white" strokeWidth={2.5} /> */}
              <img src={logo} alt="image" className="w-5 h-5"></img>
            </span>
            <span className="font-heading font-extrabold text-xl">
              LABOS <span className="text-[#085DD4]">Technologies</span>
            </span>
          </div>
          <p className="text-white/60 text-sm leading-relaxed">
            A virtual IT studio building sharp websites, apps, and keeping them healthy.
          </p>
        </div>

        <div>
          <p className="overline mb-4">Navigate</p>
          <ul className="space-y-2 text-sm text-white/70">
            <li><Link to="/" className="hover:text-[#085DD4]">Home</Link></li>
            <li><Link to="/about" className="hover:text-[#085DD4]">About</Link></li>
            <li><Link to="/services" className="hover:text-[#085DD4]">Services</Link></li>
            <li><Link to="/contact" className="hover:text-[#085DD4]">Contact</Link></li>
          </ul>
        </div>

        <div>
          <p className="overline mb-4">Services</p>
          <ul className="space-y-2 text-sm text-white/70">
            <li><Link to="/services" className="hover:text-[#085DD4]">Website Building</Link></li>
            <li><Link to="/services" className="hover:text-[#085DD4]">Site Maintenance</Link></li>
            <li><Link to="/services" className="hover:text-[#085DD4]">Application Building</Link></li>
          </ul>
        </div>

        <div>
          <p className="overline mb-4">Get in touch</p>
          <a
            href="mailto:labostechnologies.india@gmail.com"
            className="flex items-center gap-2 text-sm text-white/80 hover:text-[#085DD4]"
          >
            <Mail className="w-4 h-4" /> labostechnologies.india@gmail.com
          </a>
          <div className="flex items-center gap-3 mt-4 text-white/60">
            <a href="https://www.linkedin.com/company/labos-tech/ " aria-label="LinkedIn" className="hover:text-[#085DD4]"><Linkedin className="w-5 h-5" /></a>
            <a href="https://github.com/LABOS-Technologies" aria-label="GitHub" className="hover:text-[#085DD4]"><Github className="w-5 h-5" /></a>
          </div>
        </div>
      </div>
      <div className="border-t border-white/5 py-6 text-center text-xs text-white/50">
        © {new Date().getFullYear()} LABOS Technologies. Crafted with focus.
      </div>
    </footer>
  );
}
