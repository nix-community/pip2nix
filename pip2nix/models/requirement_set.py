from itertools import chain

from pip.req import RequirementSet
from pip.req import InstallRequirement


class ConfiguredRequirementSet(RequirementSet):
    def __init__(self, *args, **kwargs):
        self._configuration = kwargs.pop('configuration')
        super(ConfiguredRequirementSet, self).__init__(*args, **kwargs)

    def _prepare_file(self, finder, req_to_install):
        if req_to_install.constraint or req_to_install.prepared:
            return []

        print('req', req_to_install.name)

        extra_reqs = super(ConfiguredRequirementSet, self)._prepare_file(finder, req_to_install)
        setup_requires = list(from_egg_info_data(
            req_to_install.egg_info_data('setup_requires.txt'),
            comes_from=req_to_install))
        print('   ', setup_requires)
        extra_reqs.extend(chain.from_iterable(
            self.add_requirement(extra, req_to_install.name)
            for extra in setup_requires))
        return extra_reqs


class RequirementSetLayer(ConfiguredRequirementSet):
    def __init__(self, *args, **kwargs):
        self.base_requirement_set = kwargs.pop('base')
        kwargs.setdefault('configuration', self.base_requirement_set._configuration)
        kwargs.setdefault('build_dir', self.base_requirement_set.build_dir)
        kwargs.setdefault('src_dir', self.base_requirement_set.src_dir)
        kwargs.setdefault('download_dir', self.base_requirement_set.download_dir)
        kwargs.setdefault('upgrade', self.base_requirement_set.upgrade)
        kwargs.setdefault('as_egg', self.base_requirement_set.as_egg)
        kwargs.setdefault('ignore_installed', self.base_requirement_set.ignore_installed)
        kwargs.setdefault('ignore_dependencies', self.base_requirement_set.ignore_dependencies)
        kwargs.setdefault('force_reinstall', self.base_requirement_set.force_reinstall)
        kwargs.setdefault('use_user_site', self.base_requirement_set.use_user_site)
        kwargs.setdefault('target_dir', self.base_requirement_set.target_dir)
        kwargs.setdefault('session', self.base_requirement_set.session)
        kwargs.setdefault('pycompile', self.base_requirement_set.pycompile)
        kwargs.setdefault('isolated', self.base_requirement_set.isolated)
        kwargs.setdefault('wheel_cache', self.base_requirement_set._wheel_cache)
        super(RequirementSetLayer, self).__init__(*args, **kwargs)

    def _prepare_file(self, finder, req_to_install):
        if self.base_requirement_set.has_requirement(req_to_install.name):
            base_req = self.base_requirement_set.requirements[req_to_install.name]
            base_pkg_info = base_req.pkg_info()
            if not req_to_install.specifier.contains(base_pkg_info['Version']):
                # TODO: exceptions
                raise AssertionError(
                    ('There is already {req_name}=={base_pkg_version} downloaded, '
                     'but {comes_from} requires {req_name}{req_spec}')
                    .format(
                        req_name=req_to_install.name,
                        req_spec=req_to_install.specifier,
                        base_pkg_version=base_pkg_info['Version'],
                        comes_from=req_to_install.comes_from.name))
            return []
        else:
            extras = super(RequirementSetLayer, self) \
                ._prepare_file(finder, req_to_install)
            return extras



def from_egg_info_data(data, **kwargs):
    """yield requirements based on `data`"""
    # TODO: move to some common utils?
    data = data or ''
    for line in filter(None, data.splitlines()):
        yield InstallRequirement.from_line(line, **kwargs)
