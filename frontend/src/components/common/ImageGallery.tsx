import React, { useState } from "react";

interface ImageGalleryProps {
  images: string[]; // an array of image URLs
}

const ImageGallery: React.FC<ImageGalleryProps> = ({ images }) => {
  const [currentIndex, setCurrentIndex] = useState(0);

  const handleNext = () => {
    setCurrentIndex((currentIndex + 1) % images.length);
  };

  const handlePrev = () => {
    setCurrentIndex(currentIndex === 0 ? images.length - 1 : currentIndex - 1);
  };

  return (
    <div className='image-gallery'>
      <img src={images[currentIndex]} alt='gallery' />
      <button onClick={handlePrev}>Previous</button>
      <span>
        {currentIndex + 1} of {images.length} images
      </span>
      <button onClick={handleNext}>Next</button>
    </div>
  );
};

export default ImageGallery;
