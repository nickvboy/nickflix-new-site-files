import { DollarSign, Monitor, Layout } from "lucide-react";
import { FC } from 'react';

interface TeamMember {
  name: string;
  role: string;
  imageUrl: string;
  imageAlt: string;
}

interface ValueCard {
  title: string;
  description: string;
  icon: JSX.Element;
}

interface FeatureSection {
  title: {
    start: string;
    highlight: string;
    end: string;
  };
  description: string;
  imageUrl: string;
  imageAlt: string;
}

const teamMembers: TeamMember[] = [
  {
    name: "Nicholas Villiers",
    role: "Founder & CEO",
    imageUrl: "https://mail.google.com/mail/u/0?ui=2&ik=9bae6faecf&attid=0.1&permmsgid=msg-a:r-6407363204738639897&th=194d2b5dabf0ec65&view=att&disp=safe&realattid=194d2b5d2b2ebfc94901&zw",
    imageAlt: "Nicholas Villiers"
  },
  {
    name: "Michael Chen",
    role: "Lead Developer",
    imageUrl: "https://images.unsplash.com/photo-1519085360753-af0119f7cbe7",
    imageAlt: "Michael Chen"
  },
  {
    name: "Claude Villiers",
    role: "Product Designer",
    imageUrl: "https://fgcu360.com/wp-content/uploads/sites/1/2022/06/STEM-FGLSAMP-Villers-640.jpg",
    imageAlt: "Nicholas Villiers"
  },
  
  
];

const valueCards: ValueCard[] = [
  {
    title: "Improved Pricing",
    description: "Get the best deals with our smart pricing system that adapts to market trends and offers competitive rates for all movie experiences.",
    icon: <DollarSign className="w-5 h-5 text-primary-300" />
  },
  {
    title: "Easy Accessibility",
    description: "Access your favorite movies across all devices with our responsive platform designed for seamless viewing on any screen size.",
    icon: <Monitor className="w-5 h-5 text-primary-300" />
  },
  {
    title: "User-Centric Design",
    description: "Experience our thoughtfully crafted interface that puts your needs first, making movie selection and booking a breeze.",
    icon: <Layout className="w-5 h-5 text-primary-300" />
  }
];

const featureSections: FeatureSection[] = [
  {
    title: {
      start: "A",
      highlight: "Seamless",
      end: "Way to Book"
    },
    description: "Enjoy a hassle-free movie booking experience with NICKFLIX. Our platform ensures you can find your favorite movies, book tickets effortlessly, and have an unforgettable cinematic experience.",
    imageUrl: "https://i.imgur.com/4jTkV2b.png",
    imageAlt: "Cinema booking experience"
  },
  {
    title: {
      start: "Making Movies",
      highlight: "Accessible",
      end: "to Everyone"
    },
    description: "We believe everyone deserves access to quality entertainment. Our platform provides a seamless interface, adaptive features, and inclusive options to make movie-watching enjoyable for all.",
    imageUrl: "https://th.bing.com/th/id/R.562e4449cbf99b2982b0c40deb641ddf?rik=%2fU06OlHoJGvK%2bg&riu=http%3a%2f%2fwww.econlife.com%2fwp-content%2fuploads%2f2014%2f07%2fSuply-and-demand-movie-theater-seats.jpg..jpg&ehk=SAdP3JloV8yVjNtlNVfMpZxtWRxE8dEtwVUXpAgPtOI%3d&risl=&pid=ImgRaw&r=0",
    imageAlt: "Accessible movie experience"
  }
];

export const About: FC = () => {
  return (
    <main className="min-h-screen bg-bg-100 pt-16">
      <div className="max-w-4xl mx-auto p-8">
        {/* Hero Section */}
        <section className="text-center mb-16">
          <h1 className="text-h2 text-text-100 mb-4">Welcome to NICKFLIX</h1>
          <p className="text-lg text-text-200">
            Watch your favorite movies anytime, anywhere!
          </p>
        </section>

        {/* Features Section */}
        <section className="space-y-16 mb-16">
          {featureSections.map((feature, index) => (
            <div key={feature.title.highlight} className="flex flex-col md:flex-row gap-8 items-center">
              <div className={`w-full md:flex-1 space-y-4 ${index === 1 ? 'order-1 md:order-2' : ''}`}>
                <h2 className="text-h3">
                  <span className="text-primary-200">{feature.title.start}</span>{" "}
                  <span className="text-primary-300">{feature.title.highlight}</span>{" "}
                  <span className="text-primary-200">{feature.title.end}</span>
                </h2>
                <p className="text-base text-text-200">{feature.description}</p>
              </div>
              <div className={`w-full md:flex-1 ${index === 1 ? 'order-2 md:order-1' : ''}`}>
                <div className="relative h-64 rounded-lg overflow-hidden">
                  <img
                    src={feature.imageUrl}
                    alt={feature.imageAlt}
                    className="object-cover w-full h-full"
                  />
                </div>
              </div>
            </div>
          ))}
        </section>

        {/* Core Values Section */}
        <section className="mb-16">
          <div className="flex flex-col md:flex-row gap-8">
            <div className="w-full md:w-1/2">
              <h2 className="text-h3 mb-4">
                <span className="text-primary-200">Our Core</span>{" "}
                <span className="text-primary-300">Values</span>
              </h2>
              <p className="text-base text-text-200">
                Founded with a deep appreciation for cinema and making the moviegoing experience effortless, Nickflix was created to remove frustrations from booking tickets. We focus on clarity, simplicity, and ease so you can enjoy the film without unnecessary hassle.
              </p>
            </div>
            <div className="w-full md:w-1/2 space-y-4">
              {valueCards.map((card) => (
                <div key={card.title} className="bg-bg-200 rounded-xl p-6">
                  <div className="flex items-center gap-4 mb-4">
                    <div className="w-8 h-8 flex items-center justify-center bg-primary-300/10 rounded">
                      {card.icon}
                    </div>
                    <h3 className="text-h4 text-text-100">{card.title}</h3>
                  </div>
                  <p className="text-sm text-text-200">{card.description}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Team Section */}
        <section>
          <h2 className="text-h3 mb-8">
            <span className="text-primary-200">Our</span>{" "}
            <span className="text-primary-300">Team</span>
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {teamMembers.map((member) => (
              <div key={member.name} className="bg-bg-200 rounded-lg overflow-hidden">
                <div className="aspect-square">
                  <img
                    src={member.imageUrl}
                    alt={member.imageAlt}
                    className="w-full h-full object-cover"
                  />
                </div>
                <div className="p-4 text-center">
                  <h3 className="text-h4 text-text-100">{member.name}</h3>
                  <p className="text-sm text-text-200">{member.role}</p>
                </div>
              </div>
            ))}
          </div>
        </section>
      </div>
    </main>
  );
}; 