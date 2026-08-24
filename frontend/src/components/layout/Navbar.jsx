import { Link, NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";
import { Menu, X, Zap } from "lucide-react";
import { useState } from "react";

const links = [
  { to: "/", label: "Home" },
  { to: "/about", label: "About" },
  { to: "/services", label: "Services" },
  { to: "/contact", label: "Contact" },
];

export default function Navbar() {
  const { user, logout } = useAuth();
  const [open, setOpen] = useState(false);
  const navigate = useNavigate();

  const handleLogout = async () => {
    await logout();
    navigate("/");
  };

  return (
    <header className="sticky top-0 z-50 bg-black/70 backdrop-blur-xl border-b border-white/10">
      <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
        <Link to="/" className="flex items-center gap-2 group" data-testid="nav-logo-link">
          <span className="w-9 h-9 grid place-items-center bg-[#FF7A00] group-hover:bg-[#E66D00] transition-colors">
            <Zap className="w-5 h-5 text-black" strokeWidth={2.5} />
          </span>
          <span className="font-heading font-extrabold text-xl tracking-tight">
            LABOS<span className="text-[#FF7A00]">.</span>
          </span>
        </Link>

        <nav className="hidden md:flex items-center gap-8">
          {links.map((l) => (
            <NavLink
              key={l.to}
              to={l.to}
              end={l.to === "/"}
              data-testid={`nav-link-${l.label.toLowerCase()}`}
              className={({ isActive }) =>
                `text-sm font-medium tracking-wide transition-colors ${
                  isActive ? "text-[#FF7A00]" : "text-white/80 hover:text-white"
                }`
              }
            >
              {l.label}
            </NavLink>
          ))}
        </nav>

        <div className="hidden md:flex items-center gap-3">
          {user ? (
            <>
              <Link
                to={user.role === "admin" ? "/admin" : "/dashboard"}
                data-testid="nav-dashboard-btn"
                className="btn-outline text-sm"
              >
                {user.role === "admin" ? "Admin" : "Dashboard"}
              </Link>
              <button onClick={handleLogout} data-testid="nav-logout-btn" className="btn-primary text-sm">
                Logout
              </button>
            </>
          ) : (
            <>
              <Link to="/login" data-testid="nav-login-btn" className="btn-outline text-sm">
                Login
              </Link>
              <Link to="/register" data-testid="nav-register-btn" className="btn-primary text-sm">
                Get Started
              </Link>
            </>
          )}
        </div>

        <button
          className="md:hidden text-white"
          onClick={() => setOpen(!open)}
          data-testid="nav-mobile-toggle"
        >
          {open ? <X /> : <Menu />}
        </button>
      </div>

      {open && (
        <div className="md:hidden border-t border-white/10 bg-black/95">
          <div className="px-6 py-6 flex flex-col gap-4">
            {links.map((l) => (
              <NavLink
                key={l.to}
                to={l.to}
                end={l.to === "/"}
                onClick={() => setOpen(false)}
                className={({ isActive }) =>
                  `text-base font-medium ${isActive ? "text-[#FF7A00]" : "text-white/80"}`
                }
                data-testid={`nav-mobile-${l.label.toLowerCase()}`}
              >
                {l.label}
              </NavLink>
            ))}
            <div className="pt-4 border-t border-white/10 flex gap-3">
              {user ? (
                <>
                  <Link
                    to={user.role === "admin" ? "/admin" : "/dashboard"}
                    onClick={() => setOpen(false)}
                    className="btn-outline text-sm flex-1 justify-center"
                  >
                    {user.role === "admin" ? "Admin" : "Dashboard"}
                  </Link>
                  <button
                    onClick={() => {
                      setOpen(false);
                      handleLogout();
                    }}
                    className="btn-primary text-sm flex-1 justify-center"
                  >
                    Logout
                  </button>
                </>
              ) : (
                <>
                  <Link to="/login" onClick={() => setOpen(false)} className="btn-outline text-sm flex-1 justify-center">
                    Login
                  </Link>
                  <Link to="/register" onClick={() => setOpen(false)} className="btn-primary text-sm flex-1 justify-center">
                    Sign Up
                  </Link>
                </>
              )}
            </div>
          </div>
        </div>
      )}
    </header>
  );
}
