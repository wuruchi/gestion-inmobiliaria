import React from "react";
import SearchControl from "../components/search/SearchControl";
import SearchResults from "../components/search/SearchResults";

type Props = {};

const SearchScreen = (props: Props) => {
  return (
    <>
      <SearchControl />
      <SearchResults />
    </>
  );
};

export default SearchScreen;
