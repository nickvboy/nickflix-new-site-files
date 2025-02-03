import { Link } from "react-router-dom";

export function Footer() {
  return (
    <footer className="bg-bg-300 border-t border-primary-200/20">
      <div className="max-w-[1400px] mx-auto px-4 py-8">
        <div className="flex flex-col md:flex-row justify-between mb-8">
          {/* Left Section - Logo and Navigation */}
          <div className="flex flex-col gap-4">
            {/* Logo */}
            <div className="flex items-center gap-3">
              <img
                src="https://i.postimg.cc/c1gyWqs1/nickflix.png"
                alt="Nickflix Logo"
                className="h-12 w-auto object-contain"
              />
              <span className="text-h3 text-text-100 font-bold">NICKFLIX</span>
            </div>

            {/* Navigation Links */}
            <div className="flex gap-6 flex-wrap">
              <Link to="/about" className="text-text-200 hover:text-accent-200 transition-colors">About</Link>
              <Link to="/careers" className="text-text-200 hover:text-accent-200 transition-colors">Careers</Link>
              <Link to="/contact" className="text-text-200 hover:text-accent-200 transition-colors">Contact</Link>
              <Link to="/support" className="text-text-200 hover:text-accent-200 transition-colors">Support</Link>
            </div>
          </div>

          {/* Right Section - Newsletter */}
          <div className="flex flex-col items-start md:items-end gap-2">
            <span className="text-text-200 text-sm">
              Get The NICKFLIX Files Newsletter to get access to news about new releases and discounts
            </span>
            <div className="flex gap-2 w-full md:w-fit">
              <input
                type="email"
                placeholder="Enter Email"
                className="w-full md:w-auto px-4 py-2 bg-bg-100 border border-primary-200 rounded-md text-text-100 focus:outline-none focus:ring-1 focus:ring-primary-200"
              />
              <button className="px-6 py-2 bg-accent-100 hover:bg-primary-200 text-text-100 rounded-md transition-colors">
                Subscribe
              </button>
            </div>
          </div>
        </div>

        {/* Bottom Bar */}
        <div className="pt-4 border-t border-primary-200/20">
          <div className="flex flex-col md:flex-row items-center gap-2 md:gap-4 text-sm text-text-200">
            <p className="text-text-200 text-sm">
              ©2024 NICKFLIX, LLC, All Rights Reserved
            </p>
            <span className="hidden md:inline">|</span>
            <Link to="/terms" className="hover:text-accent-200 transition-colors">Terms & Conditions</Link>
            <span className="hidden md:inline text-text-200">|</span>
            <Link to="/accountability" className="hover:text-accent-200 transition-colors">Accountability Statement</Link>
          </div>
        </div>
      </div>
    </footer>
  );
} 