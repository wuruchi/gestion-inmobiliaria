import React from "react";

type Props = {
  fnPrevious: () => void;
  currentPage: number;
  maxPage: number;
  fnNext: () => void;
};

const Pagination = (props: Props) => {
  return (
    <div>
      <button
        onClick={() => props.fnPrevious()}
        disabled={props.currentPage === 1}
      >
        Previous
      </button>
      <button>{"Page " + props.currentPage + " of " + props.maxPage}</button>
      <button
        onClick={() => props.fnNext()}
        disabled={props.currentPage >= props.maxPage}
      >
        Next
      </button>
    </div>
  );
};

export default Pagination;
