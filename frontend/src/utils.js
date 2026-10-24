export const inmuebleTypes = {
  ventas: "Ventas",
  habituales: "Habituales",
  temporales: "Temporales",
  todos: "Todos",
};

export function stickyNav(distance = 700) {
  // Sticky Navigation
  const sectionHeroEl = document.querySelector(".section-hero");
  // const sectionSearchBar = document.querySelector(".section-search");
  // const sectionInmueble = document.querySelector(".inmueble-first-block");
  //  console.log(distance);
  const sectionNavEl = document.querySelector("header");
  if (sectionHeroEl && sectionNavEl) {
    const observer = new IntersectionObserver(
      (entries) => {
        const ent = entries[0];
        const screenWidth = window.innerWidth;
        // console.log(screenWidth);
        if (ent.isIntersecting === false) {
          document.body.classList.add("sticky");
        }
        if (ent.isIntersecting === true && screenWidth > distance) {
          document.body.classList.remove("sticky");
        }
      },
      {
        // In the viewport
        root: null,
        threshold: 0,
        rootMargin: "-80px",
      }
    );

    observer.observe(sectionHeroEl);
  }
  // const screenWidth = window.innerWidth;
  // if (screenWidth <= 944) {
  //   // console.log("Added");
  //   document.body.classList.add("sticky");
  // }
}

export const observerCallbackFunction = (entries) => {
  const [entry] = entries;
  if (entry.isIntersecting === false) {
    document.body.classList.add("sticky");
  } else {
    document.body.classList.remove("sticky");
  }
};

export const formatNumberMoney = (
  money,
  integerFormat = false,
  decimals = 2
) => {
  const moneyToFormat =
    money && Number.isFinite(parseFloat(money)) ? parseFloat(money) : 0.0;
  const floatFormat = moneyToFormat
    .toFixed(integerFormat === true ? 2 : decimals)
    .replace(/\d(?=(\d{3})+\.)/g, "$&,");
  if (integerFormat === false) {
    return floatFormat;
  } else {
    // Does it hold?
    return floatFormat.substr(0, floatFormat.length - 3);
  }
};

export const filterInmuebles = (
  inmuebles,
  zona,
  numberBedrooms,
  minArea,
  maxPrice
) => {
  let result = [];
  numberBedrooms = Number.parseInt(numberBedrooms);
  if (inmuebles && inmuebles.length > 0) {
    inmuebles.forEach((item) => {
      if (
        (zona === "Todas" || item.zona === zona) &&
        (numberBedrooms === 0 ||
          Number.parseInt(item.n_habitaciones) ===
            Number.parseInt(numberBedrooms)) &&
        Number.parseInt(item.sup_util) >= Number.parseInt(minArea) &&
        Number.parseFloat(item.importe_alquiler) <= Number.parseFloat(maxPrice)
      ) {
        result.push(item);
      }
    });
  }
  return result;
};
