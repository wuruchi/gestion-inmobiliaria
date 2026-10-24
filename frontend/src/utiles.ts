import { ProductoImage } from "./features/interfaces";

export const truncate = (
    str: string | undefined | null,
    length: number = 50
) => {
    if (str === undefined || str === null || str === "") {
        return "";
    }
    if (str.length > length) {
        return str.slice(0, length) + "...";
    }
    return str;
};

// write a function that gets the first item from an array if the array is not empty
export const firstImage = (arr: ProductoImage[]) => {
    if (arr.length > 0) {
        return arr[0];
    }
    return undefined;
};

export const toIntOrZero = (str?: string) => {
    if (str === undefined) {
        return 0;
    }
    if (isNaN(parseInt(str))) {
        return 0;
    }
    return parseInt(str);
};

export const toIntOrNull = (str?: string) => {
    if (str === undefined) {
        return null;
    }
    if (isNaN(parseInt(str))) {
        return null;
    }
    return parseInt(str);
};

export function formatNumber(num: number): string {
    const [integerPart, decimalPart] = num.toFixed(2).split(".");
    const formattedIntegerPart = integerPart.replace(
        /\B(?=(\d{3})+(?!\d))/g,
        ","
    );
    return `${formattedIntegerPart}.${decimalPart}`;
}

export function fomatNumberWithoutDecimalPart(strNumber: string): string {
    try {
        const [integerPart] = strNumber.split(".");
        const formattedIntegerPart = integerPart.replace(
            /\B(?=(\d{3})+(?!\d))/g,
            ","
        );
        return `${formattedIntegerPart}`;
    } catch (error) {
        console.log(error);
        return strNumber;
    }
}

/**
 * converts a date string to a date object
 * @param dateString
 * @returns empty if dateString is undefined or empty
 */
export function convertToDateOnly(dateString?: string | null): string {
    if (!dateString || dateString === "") {
        return "";
    }
    const date = new Date(dateString);
    if (isNaN(date.getTime())) {
        throw new Error("Invalid date string");
    }
    const year = date.getUTCFullYear();
    const month = String(date.getUTCMonth() + 1).padStart(2, "0");
    const day = String(date.getUTCDate()).padStart(2, "0");
    return `${year}-${month}-${day}`;
}

/**
 * function that takes the page to the top when it loads
 */
export function scrollToTop() {
    window.scrollTo({
        top: 0,
        behavior: "smooth",
    });
}

export const scrollToSection = (id: string) => {
    const element = document.getElementById(id);
    if (element) {
        const offsetTop = element.offsetTop;
        window.scrollTo({
            top: offsetTop,
            behavior: "smooth",
        });
    }
};
