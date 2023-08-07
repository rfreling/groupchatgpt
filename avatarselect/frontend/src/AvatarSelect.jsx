import React, { useEffect, useState } from "react"
import { withStreamlitConnection, Streamlit } from "streamlit-component-lib"

const AvatarSelect = ({ args }) => {
  const defaultChosen = []
  const [chosenCharacters, setChosenCharacters] = useState(defaultChosen)

  useEffect(() => Streamlit.setFrameHeight())

  useEffect(() => Streamlit.setComponentValue(defaultChosen), [])

  const onClickCharacter = (character) => {
    let _chosenCharacters = chosenCharacters
    if (chosenCharacters.includes(character)) {
      _chosenCharacters = chosenCharacters.filter((c) => c !== character)
    } else {
      _chosenCharacters = [...chosenCharacters, character]
    }

    if (_chosenCharacters.length < 5) {
      setChosenCharacters(_chosenCharacters)
      Streamlit.setComponentValue(_chosenCharacters)
    }
  }

  return (
    <div>
      <div
        style={{
          display: "flex",
          flexWrap: "wrap",
        }}
      >
        {Object.values(args.characters).map((character, index) => {
          const chosen = chosenCharacters.includes(character.value)
          return (
            <div>
              <img
                style={{
                  cursor: "pointer",
                  padding: "12px",
                  border: chosen
                    ? "8px solid lightblue"
                    : "8px solid transparent",
                  borderRadius: "50%",
                  textAlign: "center",
                }}
                onClick={() => onClickCharacter(character.value)}
                key={index}
                src={character["avatar"]}
                alt={character.display_name}
                title={character.display_name}
                width="80"
                height="80"
              />
            </div>
          )
        })}
      </div>
    </div>
  )
}

export default withStreamlitConnection(AvatarSelect)
