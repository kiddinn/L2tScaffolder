# -*- coding: utf-8 -*-
"""The scaffolder engine."""
import logging
import os

from typing import Iterator
from typing import Type

from plasoscaffolder.definitions import manager
from plasoscaffolder.lib import errors
from plasoscaffolder.lib import file_handler
from plasoscaffolder.scaffolders import interface as scaffolder_interface


class ScaffolderEngine:
  """The engine, responsible for file handling and setting up scaffolders."""

  def __init__(self):
    """Initializes the engine."""
    super(ScaffolderEngine, self).__init__()
    self._attributes = {}
    self._definition = ''
    self._definition_root_path = ''
    self._file_handler = file_handler.FileHandler()
    self._file_name_prefix = ''
    self._module_name = ''
    self._scaffolder = None

  def _RaiseIfNotReady(self):
    """Checks to see if all attributes are set to start generating files.

    Raises:
      errors.EngineNotConfigured: when the engine is not fully configured.
    """
    if not self._definition_root_path:
      raise errors.EngineNotConfigured(
          'The path to the project root is not properly configured.')

    if not self._module_name:
      raise errors.EngineNotConfigured('Module name has not been configured.')

    if not self._scaffolder:
      raise errors.EngineNotConfigured('Scaffolder object not yet set.')

    try:
      self._scaffolder.RaiseIfNotReady()
    except errors.ScaffolderNotConfigured as exception:
      raise errors.EngineNotConfigured(exception)

  def GenerateFiles(self) -> Iterator[str]:
    """Generates needed files.

    Raises:
      errors.EngineNotConfigured: when not all attributes have been configured.

    Yields:
      str: the full path to a file that was generated and written to disk.
    """
    self._RaiseIfNotReady()

    self._scaffolder.SetOutputName(self._file_name_prefix)

    for file_source, file_destination in self._scaffolder.GetFilesToCopy():
      if os.path.isfile(file_source):
        full_path = os.path.join(self._definition_root_path, file_destination)
        try:
          written_file = self._file_handler.CopyFile(file_source, full_path)
          yield written_file
        except errors.FileHandlingError as exception:
          logging.error(
              'Unable to copy file: {0:s} to {1:s} with error: {2!s}'.format(
                  file_source, full_path, exception))

    for file_path, content in self._scaffolder.GenerateFiles():
      full_path = os.path.join(self._definition_root_path, file_path)
      yield self._file_handler.AddContent(full_path, content)

  def SetModuleName(self, module_name: str):
    """Sets the module name as chosen by the user.

    Args:
      module_name (str): name of the module to be generated by the scaffolder.
    """
    self._file_name_prefix = module_name.replace(' ', '_').lower()
    self._module_name = self._file_name_prefix.replace(
        '_', ' ').title().replace(' ', '')

  def SetScaffolder(self, scaffolder: scaffolder_interface.Scaffolder):
    """Stores and initializes the scaffolder object in the engine.

    Args:
      scaffolder (scaffolder_interface.Scaffolder): the scaffolder class
          that the engine will use to generate files.
    """
    self._scaffolder = scaffolder

  def SetProjectRootPath(self, root_path: str):
    """Sets the path to the root of the project tree.

    Raises:
      errors.NoValidDefinition: when root path is not identified as a valid
          definition path.
    """
    for definition in manager.DefinitionManager.GetDefinitionObjects():
      if definition.ValidatePath(root_path):
        self._definition = definition.NAME
        self._definition_root_path = root_path
        return

    raise errors.NoValidDefinition('No valid definition has been identified.')

  def StoreScaffolderAttribute(
      self, name: str, value: object, value_type: Type):
    """Stores an attribute read from the CLI.

    Args:
      name (str): the attribute name.
      value (object): the attribute value.
      value_type (type): the attribute type.

    Raises:
      KeyError: if the attribute name is already defined.
      ScaffolderNotConfigured: if the scaffolder has not yet been set.
      ValueError: if the value is not of the correct type.
    """
    if not self._scaffolder:
      raise errors.ScaffolderNotConfigured('Scaffolder has not yet been set.')

    self._scaffolder.SetAttribute(name, value, value_type)
