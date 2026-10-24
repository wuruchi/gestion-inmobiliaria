import React from "react";

type Props = { description_es?: string };

const ProductoDescription = (props: Props) => {
  return (
    <div className='producto-description'>
      <h2>Descripción</h2>
      <p>{props.description_es}</p>
    </div>
  );
};

export default ProductoDescription;
