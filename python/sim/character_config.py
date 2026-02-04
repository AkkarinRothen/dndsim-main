"""
Character configuration system for creating pre-built character templates.

This module provides a flexible system for defining character builds that can
be instantiated at different levels.
"""
from typing import Callable, Any, Dict, Optional


class CharacterConfig:
    """
    Configuration template for creating characters.
    
    Stores a constructor function and arguments that can be used to create
    character instances at specified levels. Useful for testing different
    builds or comparing character power levels.
    
    Attributes:
        name: Display name for this character configuration
        constructor: Function that creates a Character instance
        args: Keyword arguments to pass to constructor
    
    Example:
        >>> def make_fighter(level, **kwargs):
        ...     return Character(level, stats=[16,14,15,10,12,8], **kwargs)
        >>> 
        >>> fighter_config = CharacterConfig(
        ...     name="Champion Fighter",
        ...     constructor=make_fighter,
        ...     spellcaster=Spellcaster.NONE
        ... )
        >>> 
        >>> fighter_5 = fighter_config.create(5)
        >>> fighter_10 = fighter_config.create(10)
    """
    
    def __init__(
        self,
        name: str,
        constructor: Callable[..., "sim.character.Character"],
        **kwargs: Any
    ):
        """
        Initialize character configuration.
        
        Args:
            name: Descriptive name for this build
            constructor: Function that creates a Character
            **kwargs: Additional arguments to pass to constructor
        """
        self.name = name
        self.constructor = constructor
        self.args: Dict[str, Any] = kwargs

    def create(self, level: int) -> "sim.character.Character":
        """
        Create a character instance at specified level.
        
        Args:
            level: Character level to create (1-20)
            
        Returns:
            New Character instance
            
        Raises:
            ValueError: If level is invalid
            
        Example:
            >>> config = CharacterConfig("Fighter", make_fighter)
            >>> char = config.create(level=5)
        """
        if not 1 <= level <= 20:
            raise ValueError(f"Level must be 1-20, got {level}")
        
        # Import here to avoid circular dependency
        import sim.character
        
        character = self.constructor(level, **self.args)
        
        # Set name from config if character doesn't have custom name
        if character.name == "Unnamed Character":
            character.name = self.name
        
        return character
    
    def __repr__(self) -> str:
        """String representation showing config name."""
        return f"CharacterConfig(name='{self.name}')"
    
    def __str__(self) -> str:
        """User-friendly string representation."""
        return self.name


class CharacterLibrary:
    """
    Collection of character configurations for easy access.
    
    Maintains a registry of named character builds that can be retrieved
    and instantiated on demand.
    
    Example:
        >>> library = CharacterLibrary()
        >>> library.register(fighter_config)
        >>> library.register(wizard_config)
        >>> 
        >>> fighter = library.create("Champion Fighter", level=5)
    """
    
    def __init__(self):
        """Initialize empty character library."""
        self._configs: Dict[str, CharacterConfig] = {}
    
    def register(self, config: CharacterConfig) -> None:
        """
        Add a character configuration to library.
        
        Args:
            config: CharacterConfig to register
            
        Raises:
            ValueError: If config name already exists
        """
        if config.name in self._configs:
            raise ValueError(
                f"Character config '{config.name}' already registered"
            )
        
        self._configs[config.name] = config
    
    def get(self, name: str) -> Optional[CharacterConfig]:
        """
        Retrieve a character configuration by name.
        
        Args:
            name: Name of the configuration
            
        Returns:
            CharacterConfig if found, None otherwise
        """
        return self._configs.get(name)
    
    def create(self, name: str, level: int) -> "sim.character.Character":
        """
        Create a character from library at specified level.
        
        Args:
            name: Name of the character configuration
            level: Character level to create
            
        Returns:
            New Character instance
            
        Raises:
            KeyError: If configuration name not found
            ValueError: If level is invalid
        """
        if name not in self._configs:
            available = ", ".join(self._configs.keys())
            raise KeyError(
                f"Character config '{name}' not found. "
                f"Available: {available}"
            )
        
        config = self._configs[name]
        return config.create(level)
    
    def list_configs(self) -> list[str]:
        """
        Get list of all registered configuration names.
        
        Returns:
            List of configuration names
        """
        return list(self._configs.keys())
    
    def __contains__(self, name: str) -> bool:
        """Check if configuration exists in library."""
        return name in self._configs
    
    def __len__(self) -> int:
        """Get number of registered configurations."""
        return len(self._configs)
