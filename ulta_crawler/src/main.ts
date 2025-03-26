import { CheerioCrawler, Dataset, Sitemap, ProxyConfiguration } from "crawlee";

const crawler = new CheerioCrawler({
  // Function called for each URL
  async requestHandler({ $, request, log }) {
    
    const price = $(".ProductPricing  span:first-child")
      .text()
      .replace(/[^0-9.]/g, ""); // good thing to add would be truncate to two decimal places
    const brand_name = $(".ProductInformation h1 a").text();
    const name = $(".ProductInformation h1 span:nth-of-type(2)").text();
    const size = $(
      ".ProductVariant .ProductDimension span:nth-of-type(2)"
    ).text();
    const description = $(".ProductSummary p").text();
    const ingredients = $(".ProductDetail div:nth-child(3) p").text();
    const usage =
      $(".ProductDetail div:nth-child(2) section p").text() +
      $(".ProductDetail div:nth-child(2) section ul").text();
    const category = $(".Breadcrumbs nav#breadcrumbs ul li:last-child").text();
    const image_url = $(".ProductHero .MediaGallery img").attr("src");
    const variant = $(
      ".ProductVariant .SwatchDropDown .SwatchDropDown__nameDescription span"
    ).text();

    const payload = {
      url: request.url,
      name,
      price,
      size,
      variant,
      description,
      category,
      image_url,
      brand_name,
      scraped_from: "Ulta",
      usage,
      ingredients,
    };

    log.info(`payload created for"${request.url}"`);
    await Dataset.pushData(payload);
  },
});

const { urls } = await Sitemap.load("https://www.ulta.com/sitemap/p.xml");
await crawler.addRequests(urls);
await crawler.run();
// await crawler.run([
//   "https://www.ulta.com/p/transparen-c-pro-brightening-moisturizer-pimprod2046060",
//   "https://www.ulta.com/p/shape-tape-concealer-xlsImpprod14251035?sku=2633923",
// ]);

await Dataset.exportToCSV("OUTPUT");