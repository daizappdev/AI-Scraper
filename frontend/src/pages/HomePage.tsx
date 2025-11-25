export default function HomePage() {
  return (
    <div className="bg-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-24">
        <div className="text-center">
          <h1 className="text-4xl font-bold text-gray-900 sm:text-6xl">
            AI-Powered Web Scraping
          </h1>
          <p className="mt-6 text-xl text-gray-600 max-w-3xl mx-auto">
            Generate custom web scraping scripts automatically using AI. Just provide a URL and the data you need.
          </p>
          <div className="mt-10 flex justify-center gap-4">
            <a href="/register" className="btn-primary">
              Get Started Free
            </a>
            <a href="/login" className="btn-outline">
              Sign In
            </a>
          </div>
        </div>
      </div>
    </div>
  )
}