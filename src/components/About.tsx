export function About() {
  return (
    <main className="min-h-screen bg-bg-100 pt-16">
      <div className="max-w-4xl mx-auto p-8">
        <h1 className="text-h2 text-text-100 mb-4">About Nickflix</h1>
        <p className="text-base text-text-200 mb-8">
          Nickflix is an innovative movie ticketing platform that makes movie-going simple and intuitive.
          Our platform allows users to browse movies, select seats with an engaging seat selector,
          and purchase tickets with transparent pricing and minimal fees. In addition, our social features—
          from gifting tickets to group purchases—foster a collaborative experience for all movie fans.
        </p>
        <div className="flex items-center gap-4">
          <img
            src="https://fgcu360.com/wp-content/uploads/sites/1/2020/07/Claude-Villiers-200x183-1.jpg"
            alt="Founder"
            className="w-24 h-24 rounded-full object-cover"
          />
          <div>
            <h2 className="text-h4 text-text-100">John Doe</h2>
            <p className="text-small text-text-200">Founder & CEO</p>
          </div>
        </div>
      </div>
    </main>
  );
} 