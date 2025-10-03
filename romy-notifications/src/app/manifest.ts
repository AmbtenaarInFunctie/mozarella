import type { MetadataRoute } from "next";

export default function manifest(): MetadataRoute.Manifest {
    return {
        name: "Romy",
        short_name: "Romy",
        description:
            "Een interactieve assistent (IA) voor interactie met de Rijksoverheid",
        start_url: "/",
        display: "standalone",
        background_color: "#ffffff",
        theme_color: "#000000",
        icons: [
            {
                src: "/playstore.png",
                sizes: "any",
                type: "image/png",
            },
        ],
    };
}
