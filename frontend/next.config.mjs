// Same-origin API: browser calls /api/v1/* on the tenant subdomain, Next proxies to Django. No CORS, simple auth.
const BACKEND = process.env.BACKEND_URL || "http://127.0.0.1:8000";
export default { async rewrites() { return [{ source: "/api/:path*", destination: `${BACKEND}/api/:path*` }]; } };
